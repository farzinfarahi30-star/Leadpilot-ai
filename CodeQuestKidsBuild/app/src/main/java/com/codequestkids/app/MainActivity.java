package com.kodonest.junior;

import android.app.AlertDialog;
import android.content.Context;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

import java.util.Arrays;

public class MainActivity extends AppCompatActivity {
    private static final String PREFS = "kodonest_progress";
    private final String[] ages = {"7–9", "10–12", "13–16"};
    private SharedPreferences prefs;
    private LinearLayout root;
    private String ageBand;

    @Override protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        ageBand = prefs.getString("age", "10–12");
        home();
    }

    private TextView label(String s, float size, boolean bold) {
        TextView t = new TextView(this);
        t.setText(s); t.setTextSize(size);
        t.setTextColor(Color.rgb(31,35,64));
        t.setPadding(0,8,0,8);
        if (bold) t.setTypeface(Typeface.DEFAULT, Typeface.BOLD);
        return t;
    }

    private Button action(String s, View.OnClickListener l) {
        Button b = new Button(this);
        b.setText(s); b.setAllCaps(false); b.setOnClickListener(l);
        return b;
    }

    private void page(String title, String subtitle) {
        ScrollView scroll = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(28,24,28,30);
        root.setBackgroundColor(Color.rgb(249,248,255));
        root.addView(label(title,30,true));
        root.addView(label(subtitle,16,false));
        scroll.addView(root);
        setContentView(scroll);
    }

    private void home() {
        page("KodoNest Junior", "A calm, offline coding studio for young creators.");
        root.addView(label("Choose your learning level",20,true));
        Spinner spinner = new Spinner(this);
        spinner.setAdapter(new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_dropdown_item, ages));
        int i = Arrays.asList(ages).indexOf(ageBand);
        spinner.setSelection(i < 0 ? 1 : i);
        spinner.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            public void onNothingSelected(android.widget.AdapterView<?> p) {}
            public void onItemSelected(android.widget.AdapterView<?> p, View v, int pos, long id) {
                ageBand = ages[pos]; prefs.edit().putString("age",ageBand).apply();
            }
        });
        root.addView(spinner);
        root.addView(label("Level " + level() + "  •  " + xp() + " XP",19,true));
        root.addView(action("Learning Path", v -> learningPath()));
        root.addView(action("Logic Challenges", v -> challenges()));
        root.addView(action("Build Lab", v -> buildLab()));
        root.addView(action("Project Journal", v -> journal()));
        root.addView(action("Parent Hub", v -> parentHub()));
        root.addView(label("Designed as a native Android experience. Progress and projects stay on this device.",14,false));
    }

    private int xp(){ return prefs.getInt("xp_"+ageBand,0); }
    private int level(){ return Math.max(1, xp()/100 + 1); }

    private String[] lessons() {
        if ("7–9".equals(ageBand)) return new String[]{
                "Sequences: give instructions in order","Patterns: spot what comes next",
                "Loops: repeat a useful action","Events: make something react","Create a tiny interactive story"};
        if ("13–16".equals(ageBand)) return new String[]{
                "Variables and data models","Functions and reusable logic","Arrays and collections",
                "Debugging strategies","Design a small interactive project"};
        return new String[]{
                "Variables and values","Loops and repetition","Functions and parameters",
                "Debug a short program","Design a mini game mechanic"};
    }

    private void learningPath(){
        page("Learning Path", "Short, focused lessons you can complete offline.");
        String[] ls=lessons(); int done=prefs.getInt("lessons_"+ageBand,0);
        for(int i=0;i<ls.length;i++){
            final int n=i;
            root.addView(action((i<done?"✓ ":"")+ls[i], v -> {
                int d=prefs.getInt("lessons_"+ageBand,0);
                if(n==d){
                    d++; prefs.edit().putInt("lessons_"+ageBand,d)
                            .putInt("xp_"+ageBand,d*25).apply();
                    Toast.makeText(this,"Lesson complete • +25 XP",Toast.LENGTH_SHORT).show();
                    learningPath();
                } else if(n>d) Toast.makeText(this,"Finish the earlier lesson first.",Toast.LENGTH_SHORT).show();
            }));
        }
        root.addView(action("Back",v->home()));
    }

    private void challenges(){
        page("Logic Challenges","Solve a tiny problem, then reveal the idea behind it.");
        String[] qs = {
                "Challenge 1: A robot moves 3 steps twice. How many steps?",
                "Challenge 2: What repeats when a loop runs 4 times?",
                "Challenge 3: Which value should a score variable store?",
                "Challenge 4: What should you inspect first when code crashes?"
        };
        String[] ans = {"6 steps","The loop body","A number","The error message and the line"};
        for(int i=0;i<qs.length;i++){
            final int n=i;
            root.addView(action(qs[i],v->new AlertDialog.Builder(this)
                    .setTitle("Think it through")
                    .setMessage("Answer: "+ans[n])
                    .setPositiveButton("Got it",null).show()));
        }
        root.addView(action("Back",v->home()));
    }

    private void buildLab(){
        page("Build Lab","Create a small JavaScript idea and keep it locally.");
        EditText editor=new EditText(this);
        editor.setTypeface(Typeface.MONOSPACE);
        editor.setGravity(Gravity.TOP|Gravity.START);
        editor.setMinLines(14); editor.setTextSize(15);
        editor.setText(prefs.getString("project_"+ageBand,
                "let score = 0;\nscore += 10;\nconsole.log(score);"));
        root.addView(editor,new LinearLayout.LayoutParams(-1,-2));
        root.addView(action("Save Project",v->{
            prefs.edit().putString("project_"+ageBand,editor.getText().toString()).apply();
            Toast.makeText(this,"Project saved locally.",Toast.LENGTH_SHORT).show();
        }));
        root.addView(action("Project Journal",v->journal()));
        root.addView(action("Back",v->home()));
    }

    private void journal(){
        page("Project Journal","Keep notes about what you built and what you want to try next.");
        EditText notes=new EditText(this);
        notes.setGravity(Gravity.TOP|Gravity.START); notes.setMinLines(12);
        notes.setText(prefs.getString("notes_"+ageBand,"My next project idea:\n\nWhat I learned:\n"));
        root.addView(notes,new LinearLayout.LayoutParams(-1,-2));
        root.addView(action("Save Notes",v->{
            prefs.edit().putString("notes_"+ageBand,notes.getText().toString()).apply();
            Toast.makeText(this,"Journal saved locally.",Toast.LENGTH_SHORT).show();
        }));
        root.addView(action("Back",v->home()));
    }

    private void parentHub(){
        page("Parent Hub","Simple local progress information with no account required.");
        int total=0;
        for(String a:ages) total+=prefs.getInt("xp_"+a,0);
        root.addView(label("Current level: "+level()+"\nCurrent XP: "+xp()+
                "\nAll-level XP: "+total+
                "\n\nKodoNest Junior stores learning progress locally on this device.",17,false));
        root.addView(action("Reset Local Progress",v->new AlertDialog.Builder(this)
                .setTitle("Reset all local progress?")
                .setMessage("This removes KodoNest Junior lessons, projects and notes from this device.")
                .setNegativeButton("Cancel",null)
                .setPositiveButton("Reset",(d,w)->{prefs.edit().clear().putString("age","10–12").apply();ageBand="10–12";parentHub();})
                .show()));
        root.addView(action("Back",v->home()));
    }

    @Override public void onBackPressed(){ home(); }
}
