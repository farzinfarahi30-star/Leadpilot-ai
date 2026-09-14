package com.codequestkids.app;

import android.annotation.SuppressLint;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.CookieManager;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.activity.OnBackPressedCallback;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

public class MainActivity extends AppCompatActivity {
    private static final String SITE = "https://codequest-kids.azinahi123.workers.dev";
    private static final String SITE_HOST = "codequest-kids.azinahi123.workers.dev";
    private WebView web;
    private SwipeRefreshLayout refresh;
    private View offline;
    private ValueCallback<Uri[]> filePathCallback;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        buildUi();
        configureWebView();
        refresh.setOnRefreshListener(() -> web.reload());
        getOnBackPressedDispatcher().addCallback(this, new OnBackPressedCallback(true) {
            @Override public void handleOnBackPressed() {
                if (web.canGoBack()) web.goBack(); else finish();
            }
        });
        if (state == null) web.loadUrl(SITE); else web.restoreState(state);
    }

    private void buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(Color.WHITE);
        refresh = new SwipeRefreshLayout(this);
        web = new WebView(this);
        refresh.addView(web, new SwipeRefreshLayout.LayoutParams(-1, -1));
        offline = offlineView();
        offline.setVisibility(View.GONE);
        root.addView(refresh, new LinearLayout.LayoutParams(-1, 0, 1));
        root.addView(offline, new LinearLayout.LayoutParams(-1, 0, 1));
        ViewCompat.setOnApplyWindowInsetsListener(root, (v, insets) -> {
            Insets bars = insets.getInsets(WindowInsetsCompat.Type.systemBars());
            v.setPadding(0, bars.top, 0, bars.bottom);
            return insets;
        });
        setContentView(root);
    }

    private View offlineView() {
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER);
        box.setPadding(48, 48, 48, 48);
        TextView t = new TextView(this);
        t.setText(R.string.app_name);
        t.setTextSize(28);
        t.setTextColor(Color.rgb(22, 33, 62));
        t.setGravity(Gravity.CENTER);
        TextView m = new TextView(this);
        m.setText("Couldn’t load CodeQuest Kids.\n\nCheck your internet connection and try again.");
        m.setTextSize(17);
        m.setGravity(Gravity.CENTER);
        m.setPadding(0, 20, 0, 24);
        Button b = new Button(this);
        b.setText("Try again");
        b.setOnClickListener(v -> web.loadUrl(SITE));
        box.addView(t); box.addView(m); box.addView(b);
        return box;
    }

    @SuppressLint("SetJavaScriptEnabled")
    private void configureWebView() {
        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setAllowFileAccess(false);
        s.setAllowContentAccess(false);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setTextZoom(100);
        CookieManager cookies = CookieManager.getInstance();
        cookies.setAcceptCookie(true);
        cookies.setAcceptThirdPartyCookies(web, false);
        web.setBackgroundColor(Color.WHITE);
        web.setWebChromeClient(new WebChromeClient() {
            @Override public boolean onShowFileChooser(WebView w, ValueCallback<Uri[]> callback, FileChooserParams params) {
                if (filePathCallback != null) filePathCallback.onReceiveValue(null);
                filePathCallback = callback;
                try {
                    startActivityForResult(params.createIntent(), 1001);
                    return true;
                } catch (ActivityNotFoundException e) {
                    filePathCallback = null;
                    callback.onReceiveValue(null);
                    return false;
                }
            }
        });
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest r) { return routeUrl(r.getUrl()); }
            @Override public boolean shouldOverrideUrlLoading(WebView v, String url) { return routeUrl(Uri.parse(url)); }
            @Override public void onPageFinished(WebView v, String url) { refresh.setRefreshing(false); showWeb(); }
            @Override public void onReceivedError(WebView v, WebResourceRequest r, WebResourceError e) { if (r.isForMainFrame()) showOffline(); }
        });
    }

    private boolean routeUrl(Uri uri) {
        if (uri == null) return true;
        String scheme = uri.getScheme();
        String host = uri.getHost();
        if ("https".equalsIgnoreCase(scheme) && host != null && (SITE_HOST.equalsIgnoreCase(host) || host.endsWith("." + SITE_HOST))) return false;
        if ("http".equalsIgnoreCase(scheme) || "https".equalsIgnoreCase(scheme)) {
            try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); } catch (ActivityNotFoundException ignored) {}
            return true;
        }
        try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); } catch (ActivityNotFoundException ignored) {}
        return true;
    }
    private void showWeb() { refresh.setVisibility(View.VISIBLE); offline.setVisibility(View.GONE); }
    private void showOffline() { refresh.setVisibility(View.GONE); offline.setVisibility(View.VISIBLE); }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != 1001 || filePathCallback == null) return;
        Uri[] results = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
        filePathCallback.onReceiveValue(results);
        filePathCallback = null;
    }
    @Override protected void onSaveInstanceState(Bundle out) { web.saveState(out); super.onSaveInstanceState(out); }
    @Override protected void onDestroy() { if (filePathCallback != null) filePathCallback.onReceiveValue(null); if (web != null) web.destroy(); super.onDestroy(); }
}
