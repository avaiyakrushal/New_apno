package com.apno.party;

import android.app.Activity;
import android.os.Bundle;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.Button;

public class RoomActivity extends Activity {
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(getColor(R.color.navy));
        getWindow().setNavigationBarColor(getColor(R.color.navy));
        setContentView(R.layout.activity_room);
        String name = getIntent().getStringExtra("room_name");
        ((TextView) findViewById(R.id.room_name)).setText(name == null ? "Room" : name);
        Button mic = findViewById(R.id.mic);
        mic.setOnClickListener(v -> Toast.makeText(this,
            "Live voice chat is not connected yet", Toast.LENGTH_LONG).show());
        findViewById(R.id.leave).setOnClickListener(v -> finish());
    }
}
