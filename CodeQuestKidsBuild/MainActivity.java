package com.codequestkids.app;

import android.app.*;
import android.os.Bundle;
import android.content.*;
import android.graphics.Color;
import android.net.Uri;
import android.view.*;
import android.webkit.*;
import android.widget.*;
import java.util.Arrays;

public class MainActivity extends Activity {
  static final String SITE="https://codequest-kids.azinahi123.workers.dev";
  static final String HOST="codequest-kids.azinahi123.workers.dev";
  final String[] tracks={"7–9","10–12","13–16"};
  SharedPreferences p; LinearLayout root; String track; int screen=0;

  public void onCreate(Bundle b){
    super.onCreate(b); p=getSharedPreferences("cq_progress",0);
    track=p.getString("track","10–12"); home();
  }
  TextView t(String s,int z,boolean bold){ TextView v=new TextView(this); v.setText(s);v.setTextSize(z);v.setTextColor(Color.rgb(22,33,62));v.setPadding(0,8,0,8);if(bold)v.setTypeface(null,1);return v; }
  Button btn(String s,View.OnClickListener l){Button b=new Button(this);b.setText(s);b.setAllCaps(false);b.setOnClickListener(l);return b;}
  void page(String title,String sub){ScrollView sv=new ScrollView(this);root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(30,24,30,30);root.setBackgroundColor(Color.rgb(248,250,252));root.addView(t(title,30,true));root.addView(t(sub,16,false));sv.addView(root);setContentView(sv);}
  void home(){
    screen=0;page("CodeQuest Kids","Build games. Learn code. Create the future.");
    root.addView(t("Learning track",20,true));
    Spinner sp=new Spinner(this);sp.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,tracks));
    sp.setSelection(Math.max(0,Arrays.asList(tracks).indexOf(track)));
    sp.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener(){
      public void onNothingSelected(AdapterView<?> a){} public void onItemSelected(AdapterView<?> a,View v,int pos,long id){track=tracks[pos];p.edit().putString("track",track).apply();}
    });root.addView(sp);
    int xp=p.getInt("xp_"+track,0),done=p.getInt("done_"+track,0);
    root.addView(t(xp+" XP • "+done+" missions completed",18,true));
    root.addView(btn("Missions",v->missions()));root.addView(btn("Coding Lab",v->coding()));
    root.addView(btn("Online Academy",v->online()));root.addView(btn("Parent / Guardian Progress",v->parent()));
    root.addView(t("Native offline missions, XP, track selection and saved coding projects are available without an account.",14,false));
  }
  String[] missions(){
    if(track.equals("7–9"))return new String[]{"Make a character move","Collect stars","Build a button","Tell a coding story","Create a mini game"};
    if(track.equals("13–16"))return new String[]{"Use arrays and objects","Manage game state","Handle DOM events","Debug a program","Build a mini web game"};
    return new String[]{"Use variables","Master loops","Write functions","Fix a JavaScript bug","Build a mini game"};
  }
  void missions(){
    screen=1;page("Missions • "+track,"Complete in order and earn 25 XP each.");
    String[] m=missions();int done=p.getInt("done_"+track,0);
    for(int i=0;i<m.length;i++){final int n=i;root.addView(btn((i<done?"✓ ":"")+m[i]+"  +25 XP",v->{int d=p.getInt("done_"+track,0);if(n<d)return;int next=Math.min(m.length,n+1);p.edit().putInt("done_"+track,next).putInt("xp_"+track,next*25).apply();missions();}));}
    root.addView(btn("Back to Home",v->home()));
  }
  void coding(){
    screen=2;page("Coding Lab","Write JavaScript and save your project on this device.");
    EditText e=new EditText(this);e.setGravity(Gravity.TOP|Gravity.START);e.setTextSize(15);e.setTypeface(android.graphics.Typeface.MONOSPACE);e.setMinLines(12);
    e.setText(p.getString("code_"+track,"const player = { name: \"Nova\", score: 0 };\nplayer.score += 10;\nconsole.log(player.name, player.score);"));
    root.addView(e,new LinearLayout.LayoutParams(-1,-2));
    root.addView(btn("Save Project",v->{p.edit().putString("code_"+track,e.getText().toString()).apply();Toast.makeText(this,"Project saved locally.",Toast.LENGTH_SHORT).show();}));
    root.addView(btn("Open Online Academy",v->online()));root.addView(btn("Back to Home",v->home()));
  }
  void parent(){
    screen=3;page("Parent / Guardian","Progress stored locally on this device.");
    int xp=0,done=0;for(String s:tracks){xp+=p.getInt("xp_"+s,0);done+=p.getInt("done_"+s,0);}
    root.addView(t("Current track: "+track,18,true));root.addView(t("Total XP: "+xp+"\nMissions completed: "+done+"\nNo account or advertising is required.",17,false));
    root.addView(btn("Reset Local Progress",v->new AlertDialog.Builder(this).setTitle("Reset progress?").setMessage("Only local CodeQuest Kids progress will be removed.").setNegativeButton("Cancel",null).setPositiveButton("Reset",(d,w)->{p.edit().clear().putString("track","10–12").apply();track="10–12";parent();}).show()));
    root.addView(btn("Back to Home",v->home()));
  }
  void codingWeb(WebView w){
    WebSettings s=w.getSettings();s.setJavaScriptEnabled(true);s.setDomStorageEnabled(true);s.setAllowFileAccess(false);s.setAllowContentAccess(false);s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);w.setWebChromeClient(new WebChromeClient());
  }
  void online(){
    screen=4;WebView w=new WebView(this);codingWeb(w);w.setWebViewClient(new WebViewClient(){
      public boolean shouldOverrideUrlLoading(WebView v,WebResourceRequest r){return route(r.getUrl());}
      public boolean shouldOverrideUrlLoading(WebView v,String u){return route(Uri.parse(u));}
    });setContentView(w);w.loadUrl(SITE);
  }
  boolean route(Uri u){if(u==null)return true;String s=u.getScheme(),h=u.getHost();if("https".equalsIgnoreCase(s)&&h!=null&&(HOST.equalsIgnoreCase(h)||h.endsWith("."+HOST)))return false;if("http".equalsIgnoreCase(s)||"https".equalsIgnoreCase(s)){try{startActivity(new Intent(Intent.ACTION_VIEW,u));}catch(Exception ignored){}}return true;}
  public void onBackPressed(){if(screen!=0)home();else super.onBackPressed();}
}
