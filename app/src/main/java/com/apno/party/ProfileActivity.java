package com.apno.party;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.content.Intent;
import android.net.Uri;
import android.text.InputFilter;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.TextView;
import android.widget.LinearLayout;
import android.view.View;
import android.graphics.Typeface;
import java.util.Locale;
import java.util.UUID;
import org.json.JSONArray;

public class ProfileActivity extends Activity {
    private SharedPreferences data;
    private TextView nameView;
    private ImageView photoView;
    private static final int PICK_PHOTO = 41;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(getColor(R.color.paper));
        getWindow().setNavigationBarColor(getColor(R.color.paper));
        getWindow().getDecorView().setSystemUiVisibility(android.view.View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | android.view.View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        setContentView(R.layout.activity_profile);
        data = getSharedPreferences("apno_preview", MODE_PRIVATE);
        nameView = findViewById(R.id.name);
        photoView = findViewById(R.id.profile_photo);
        String savedPhoto = data.getString("photo_uri", null);
        if (savedPhoto != null) showPhoto(Uri.parse(savedPhoto));
        nameView.setText(data.getString("name", "Your name"));
        ((TextView) findViewById(R.id.bio)).setText(data.getString("bio", "Add a short bio"));
        String id = data.getString("local_id", null);
        if (id == null) {
            id = UUID.randomUUID().toString().substring(0, 8).toUpperCase(Locale.US);
            data.edit().putString("local_id", id).apply();
        }
        ((TextView) findViewById(R.id.preview_id)).setText("Local preview ID: " + id);
        findViewById(R.id.edit_name).setOnClickListener(v -> editName());
        findViewById(R.id.edit_bio).setOnClickListener(v -> editBio());
        findViewById(R.id.choose_photo).setOnClickListener(v -> {
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.setType("image/*");
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
            startActivityForResult(intent, PICK_PHOTO);
        });
        findViewById(R.id.back).setOnClickListener(v -> finish());
        findViewById(R.id.profile_favorites).setOnClickListener(v -> showRecords(false));
        findViewById(R.id.profile_follow).setOnClickListener(v -> showRecords(true));
        findViewById(R.id.profile_tab_party).setOnClickListener(v -> goHome("party"));
        findViewById(R.id.profile_tab_game).setOnClickListener(v -> goHome("game"));
        findViewById(R.id.profile_tab_discover).setOnClickListener(v -> goHome("discover"));
        findViewById(R.id.profile_tab_messages).setOnClickListener(v -> goHome("messages"));
        findViewById(R.id.profile_tab_me).setOnClickListener(v -> showRecords(false));
        showRecords(false);
    }

    @Override protected void onResume() {
        super.onResume();
        if (data == null) return;
        int count = 0;
        try { count = new JSONArray(data.getString("posts", "[]")).length(); }
        catch (Exception ignored) { }
        ((TextView) findViewById(R.id.post_count)).setText(count + (count == 1 ? " post" : " posts"));
        showRecords(false);
    }

    private void goHome(String tab) {
        Intent intent = new Intent(this, HomeActivity.class);
        intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        intent.putExtra("open_tab", tab);
        startActivity(intent);
        finish();
    }

    private void showRecords(boolean following) {
        if (data == null) return;
        ((TextView) findViewById(R.id.profile_favorites)).setTextColor(getColor(following ? R.color.subtle : R.color.ink));
        ((TextView) findViewById(R.id.profile_follow)).setTextColor(getColor(following ? R.color.ink : R.color.subtle));
        ((TextView) findViewById(R.id.record_title)).setText(following ? "Following" : "Party Records");
        LinearLayout records = findViewById(R.id.profile_records);
        records.removeAllViews();
        if (following) {
            addRecord(records, "People you follow will appear here when accounts are connected.", false, null);
            return;
        }
        try {
            JSONArray rooms = new JSONArray(data.getString("rooms", "[]"));
            if (rooms.length() == 0) {
                addRecord(records, "No party rooms yet. Create one from the Party tab.", false, null);
                return;
            }
            for (int i = rooms.length() - 1; i >= 0; i--) {
                org.json.JSONObject room = rooms.optJSONObject(i);
                String title = room == null ? rooms.optString(i) : room.optString("title");
                String category = room == null ? "Party" : room.optString("category", "Party");
                addRecord(records, title + "\n" + category + " · On this phone", true, title);
            }
        } catch (Exception error) {
            addRecord(records, "Unable to read local rooms.", false, null);
        }
    }

    private void addRecord(LinearLayout parent, String label, boolean active, String title) {
        TextView row = new TextView(this);
        row.setText((active ? "🎙  " : "") + label);
        row.setTextColor(getColor(active ? R.color.ink : R.color.subtle));
        row.setTextSize(17);
        row.setTypeface(null, active ? Typeface.BOLD : Typeface.NORMAL);
        row.setPadding(12, 22, 12, 22);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
        params.topMargin = (int) (8 * getResources().getDisplayMetrics().density);
        parent.addView(row, params);
        if (active) row.setOnClickListener(v -> {
            Intent intent = new Intent(this, RoomActivity.class);
            intent.putExtra("room_name", title);
            startActivity(intent);
        });
    }

    private void editBio() {
        EditText input = new EditText(this);
        input.setText(data.getString("bio", ""));
        input.setHint("Tell people about yourself");
        input.setFilters(new InputFilter[] { new InputFilter.LengthFilter(160) });
        new AlertDialog.Builder(this).setTitle("Your bio").setView(input)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Save", (dialog, which) -> {
                String bio = input.getText().toString().trim();
                data.edit().putString("bio", bio).apply();
                ((TextView) findViewById(R.id.bio)).setText(bio.isEmpty() ? "Add a short bio" : bio);
            }).show();
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent result) {
        super.onActivityResult(requestCode, resultCode, result);
        if (requestCode != PICK_PHOTO || resultCode != RESULT_OK || result == null || result.getData() == null) return;
        Uri uri = result.getData();
        try {
            getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
            data.edit().putString("photo_uri", uri.toString()).apply();
            showPhoto(uri);
        } catch (SecurityException exception) {
            android.widget.Toast.makeText(this, "Could not save access to this photo", android.widget.Toast.LENGTH_LONG).show();
        }
    }

    private void showPhoto(Uri uri) {
        try { photoView.setImageURI(uri); }
        catch (Exception ignored) { photoView.setImageResource(R.drawable.apno_mark); }
    }

    private void editName() {
        EditText input = new EditText(this);
        input.setSingleLine(true);
        input.setText(data.getString("name", ""));
        input.setFilters(new InputFilter[] { new InputFilter.LengthFilter(40) });
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Your name")
            .setView(input).setNegativeButton("Cancel", null)
            .setPositiveButton("Save", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener(v -> {
                String name = input.getText().toString().trim();
                if (name.isEmpty()) { input.setError("Enter a name"); return; }
                data.edit().putString("name", name).apply();
                nameView.setText(name);
                dialog.dismiss();
            }));
        dialog.show();
    }
}
