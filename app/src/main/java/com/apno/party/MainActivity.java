package com.apno.party;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.widget.Toast;

public class MainActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(getColor(R.color.navy));
        getWindow().setNavigationBarColor(getColor(R.color.navy));
        setContentView(R.layout.activity_main);
        int[] authButtons = { R.id.google, R.id.facebook, R.id.mobile };
        for (int id : authButtons) {
            findViewById(id).setOnClickListener(v -> Toast.makeText(this,
                "Sign-in is not connected yet", Toast.LENGTH_LONG).show());
        }
        findViewById(R.id.explore).setOnClickListener(v ->
            startActivity(new Intent(this, HomeActivity.class)));
    }
}
