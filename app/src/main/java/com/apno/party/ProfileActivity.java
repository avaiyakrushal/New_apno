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
        getWindow().setStatusBarColor(getColor(R.color.navy));
        getWindow().setNavigationBarColor(getColor(R.color.navy));
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
    }

    @Override protected void onResume() {
        super.onResume();
        if (data == null) return;
        int count = 0;
        try { count = new JSONArray(data.getString("posts", "[]")).length(); }
        catch (Exception ignored) { }
        ((TextView) findViewById(R.id.post_count)).setText(count + " local posts");
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
