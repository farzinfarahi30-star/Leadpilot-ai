import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { stripTypeScriptTypes } from 'node:module';
import { execFileSync } from 'node:child_process';

// Run only against reviewed project source. Imports are stubbed: this is a
// handler-level regression check, not an HTTP/browser or full-project test.
const root = path.resolve(process.argv[2] || 'bawes-universe');
const revision = process.argv[3];
const read = (file) => revision
    ? execFileSync('git', ['-C', root, 'show', `${revision}:${file}`], {encoding: 'utf8'})
    : fs.readFileSync(path.join(root, file), 'utf8');
let source = stripTypeScriptTypes(read('play/src/pusher/controllers/FrontController.ts'), {mode: 'transform'});
source = source.replace(/^import[\s\S]*?from\s+['"][^'"]+['"];\s*/gm, '');
source = source.replace('export class FrontController', 'class FrontController');
source += '\nglobalThis.FrontController = FrontController;';
let metadata;
const context = vm.createContext({
    BaseHttpController: class {},
    Debug: () => () => {},
    MetaTagsBuilder: class { async getMeta() { return metadata; } },
});
vm.runInContext(source, context, {timeout: 1000});
const controller = Object.create(context.FrontController.prototype);
let passed = 0;
let failed = 0;
async function check(name, run) {
    try { await run(); passed++; console.log(`PASS ${name}`); }
    catch (e) { failed++; console.log(`FAIL ${name}: ${e.message}`); }
}
for (const room of ['/@/universe/lobby', '/~/community/event', '/']) {
    await check(`live handler preserves room data and uses fullscreen landscape: ${room}`, async () => {
        metadata = {title: 'Community room', themeColor: '#123456', description: 'Custom room description',
            manifestIcons: [{src: '/room-icon.png', sizes: '512x512', type: 'image/png'}]};
        let payload; let type;
        const res = {contentType(value) {type = value; return this;}, json(value) {payload = value;}};
        await controller.displayManifestJson({protocol: 'https', hostname: 'universe.example', header: () => 'Test'}, res, 'https://universe.example' + room);
        assert.equal(type, 'application/manifest+json');
        assert.equal(payload.name, metadata.title);
        assert.equal(payload.description, metadata.description);
        assert.equal(payload.theme_color, metadata.themeColor);
        assert.equal(payload.icons, metadata.manifestIcons);
        assert.equal(payload.start_url, room);
        assert.equal(payload.display, 'fullscreen');
        assert.equal(payload.orientation, 'landscape');
        assert.equal(payload.display_override, undefined);
        assert.equal(payload.related_applications, undefined);
    });
}
await check('static fallback uses Universe identity, fullscreen landscape and existing icons', () => {
    const manifest = JSON.parse(read('play/public/static/images/favicons/manifest.json'));
    assert.equal(manifest.name, 'BAWES Universe');
    assert.equal(manifest.short_name, 'Universe');
    assert.equal(manifest.display, 'fullscreen');
    assert.equal(manifest.orientation, 'landscape');
    assert.equal(manifest.display_override, undefined);
    assert.equal(manifest.related_applications, undefined);
    assert(manifest.icons.some(i => i.sizes === '192x192'));
    assert(manifest.icons.some(i => i.sizes === '512x512'));
});
console.log(JSON.stringify({passed, failed, mode: revision || 'working-tree'}));
process.exitCode = failed ? 1 : 0;
