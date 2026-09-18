package com.codequestkids.app;

import android.app.AlertDialog;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.util.Arrays;

public class MainActivity extends AppCompatActivity {
    private static final String SITE = "https://codequest-kids.azinahi123.workers.dev";
    private static final String SITE_HOST = "codequest-kids.azinahi123.workers.dev";
    private static final String PREFS = "codequest_kids_progress";

    private final String[] tracks = {"7–9", "10–12", "13–16"};
    private SharedPreferences prefs;
    private LinearLayout root;
    private String track;
    private int screen = 0;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        track = prefs.getString("track", "10–12");
        showHome();
    }

    private TextView text(String value, float size, boolean bold) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(size);
        t.setTextColor(Color.rgb(22, 33, 62));
        t.setPadding(0, 8, 0, 8);
        if (bold) t.setTypeface(null, 1);
        return t;
    }

    private Button button(String label, View.OnClickListener listener) {
        Button b = new Button(this);
        b.setText(label);
        b.setAllCaps(false);
        b.setOnClickListener(listener);
        return b;
    }

    private void page(String title, String subtitle) {
        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(30, 24, 30, 30);
        root.setBackgroundColor(Color.rgb(248, 250, 252));
        root.addView(text(title, 30, true));
        root.addView(text(subtitle, 16, false));
        scroll.addView(root);
        setContentView(scroll);
    }

    private void showHome() {
        screen = 0;
        page("CodeQuest Kids", "Build games. Learn code. Create the future.");
        root.addView(text("Learning track", 20, true));

        Spinner spinner = new Spinner(this);
        spinner.setAdapter(new ArrayAdapter<String>(
                this,
                android.R.layout.simple_spinner_dropdown_item,
                tracks
        ));
        int index = Arrays.asList(tracks).indexOf(track);
        spinner.setSelection(index >= 0 ? index : 1);
        spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onNothingSelected(AdapterView<?> parent) { }

            @Override public void onItemSelected(
                    AdapterView<?> parent, View view, int position, long id) {
                track = tracks[position];
                prefs.edit().putString("track", track).apply();
                showHomeStats();
            }
        });
        root.addView(spinner);

        root.addView(text(
                getXp() + " XP  •  " + getCompleted() + " missions completed",
                18,
                true
        ));

        root.addView(button("Missions", v -> showMissions()));
        root.addView(button("Coding Lab", v -> showCodingLab()));
        root.addView(button("Online Academy", v -> showOnlineAcademy()));
        root.addView(button("Parent / Guardian Progress", v -> showParent()));

        root.addView(text(
                "Native offline learning tools are built into the app. The official online academy is an optional connected feature.",
                14,
                false
        ));
    }

    private void showHomeStats() {
        if (screen == 0) showHome();
    }

    private int getCompleted() {
        return prefs.getInt("done_" + track, 0);
    }

    private int getXp() {
        return prefs.getInt("xp_" + track, 0);
    }

    private String[] missions() {
        if ("7–9".equals(track)) {
            return new String[]{
                    "Make a character move",
                    "Collect stars",
                    "Build a clickable button",
                    "Tell a coding story",
                    "Create a mini game"
            };
        }
        if ("13–16".equals(track)) {
            return new String[]{
                    "Use arrays and objects",
                    "Manage game state",
                    "Handle DOM events",
                    "Debug a broken program",
                    "Build a mini web game"
            };
        }
        return new String[]{
                "Use variables",
                "Master loops",
                "Write functions",
                "Fix a JavaScript bug",
                "Build a mini game"
        };
    }

    private void showMissions() {
        screen = 1;
        page("Missions • " + track, "Complete missions in order and earn 25 XP each.");

        String[] list = missions();
        int done = getCompleted();

        for (int i = 0; i < list.length; i++) {
            final int missionIndex = i;
            root.addView(button((i < done ? "✓ " : "") + list[i] + "  +25 XP", v -> {
                int current = getCompleted();
                if (missionIndex < current) {
                    Toast.makeText(this, "Already completed.", Toast.LENGTH_SHORT).show();
                    return;
                }
                if (missionIndex > current) {
                    Toast.makeText(this, "Complete the previous mission first.", Toast.LENGTH_SHORT).show();
                    return;
                }
                int next = Math.min(list.length, current + 1);
                prefs.edit()
                        .putInt("done_" + track, next)
                        .putInt("xp_" + track, next * 25)
                        .apply();
                showMissions();
            }));
        }

        root.addView(button("Back to Home", v -> showHome()));
    }

    private void showCodingLab() {
        screen = 2;
        page("Coding Lab", "Write JavaScript and save your project on this device.");

        EditText editor = new EditText(this);
        editor.setText(prefs.getString(
                "code_" + track,
                "const player = { name: \"Nova\", score: 0 };\n"
                        + "player.score += 10;\n"
                        + "console.log(player.name, player.score);"
        ));
        editor.setTextSize(15);
        editor.setGravity(Gravity.TOP | Gravity.START);
        editor.setTypeface(android.graphics.Typeface.MONOSPACE);
        editor.setMinLines(12);
        editor.setPadding(16, 16, 16, 16);
        root.addView(editor, new LinearLayout.LayoutParams(-1, -2));

        root.addView(button("Save Project", v -> {
            prefs.edit().putString("code_" + track, editor.getText().toString()).apply();
            Toast.makeText(this, "Project saved on this device.", Toast.LENGTH_SHORT).show();
        }));

        root.addView(button("Open Online Academy", v -> showOnlineAcademy()));
        root.addView(button("Back to Home", v -> showHome()));
    }

    private void showParent() {
        screen = 3;
        page("Parent / Guardian", "Learning progress is stored locally on this device.");

        int totalXp = 0;
        int totalDone = 0;
        for (String t : tracks) {
            totalXp += prefs.getInt("xp_" + t, 0);
            totalDone += prefs.getInt("done_" + t, 0);
        }

        root.addView(text("Current track: " + track, 18, true));
        root.addView(text(
                "Total XP: " + totalXp + "\n"
                        + "Missions completed: " + totalDone + "\n"
                        + "No account or advertising is required.",
                17,
                false
        ));

        root.addView(button("Reset Local Progress", v ->
                new AlertDialog.Builder(this)
                        .setTitle("Reset progress?")
                        .setMessage("Only CodeQuest Kids progress stored on this device will be removed.")
                        .setNegativeButton("Cancel", null)
                        .setPositiveButton("Reset", (dialog, which) -> {
                            prefs.edit().clear().putString("track", "10–12").apply();
                            track = "10–12";
                            showParent();
                        })
                        .show()
        ));

        root.addView(button("Back to Home", v -> showHome()));
    }

    private void showOnlineAcademy() {
        screen = 4;
        WebView web = new WebView(this);
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        web.setBackgroundColor(Color.WHITE);
        web.setWebChromeClient(new WebChromeClient());
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return routeUrl(request.getUrl());
            }
            @Override public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return routeUrl(Uri.parse(url));
            }
        });
        setContentView(web);
        web.loadUrl(SITE);
    }

    private boolean routeUrl(Uri uri) {
        if (uri == null) return true;
        String scheme = uri.getScheme();
        String host = uri.getHost();

        if ("https".equalsIgnoreCase(scheme) && host != null &&
                (SITE_HOST.equalsIgnoreCase(host) || host.endsWith("." + SITE_HOST))) {
            return false;
        }

        if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, uri));
            } catch (Exception ignored) {
                Toast.makeText(this, "Unable to open link.", Toast.LENGTH_SHORT).show();
            }
        }
        return true;
    }

    @Override
    public void onBackPressed() {
        if (screen != 0) showHome(); else super.onBackPressed();
    }
}
