package com.apno.party;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.net.Uri;
import android.os.Bundle;
import android.graphics.Color;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import android.text.InputFilter;
import org.json.JSONArray;
import org.json.JSONObject;

public class HomeActivity extends Activity {
    private static final int PICK_POST_PHOTO = 42;
    private SharedPreferences data;
    private LinearLayout rooms;
    private LinearLayout posts;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(getColor(R.color.navy));
        getWindow().setNavigationBarColor(getColor(R.color.navy));
        setContentView(R.layout.activity_home);
        data = getSharedPreferences("apno_preview", MODE_PRIVATE);
        rooms = findViewById(R.id.rooms);
        posts = findViewById(R.id.posts);
        findViewById(R.id.create_post).setOnClickListener(v -> createPost());
        findViewById(R.id.create_photo_post).setOnClickListener(v -> pickPostPhoto());
        findViewById(R.id.create_room).setOnClickListener(v -> createRoom());
        findViewById(R.id.profile).setOnClickListener(v ->
            startActivity(new Intent(this, ProfileActivity.class)));
        showRooms();
        showPosts();
    }

    private JSONArray savedPosts() {
        try { return new JSONArray(data.getString("posts", "[]")); }
        catch (Exception ignored) { return new JSONArray(); }
    }

    private void createPost() {
        composePost(null);
    }

    private void pickPostPhoto() {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType("image/*");
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(intent, PICK_POST_PHOTO);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent result) {
        super.onActivityResult(requestCode, resultCode, result);
        if (requestCode != PICK_POST_PHOTO || resultCode != RESULT_OK || result == null || result.getData() == null) return;
        Uri uri = result.getData();
        try {
            getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
            composePost(uri);
        } catch (SecurityException exception) {
            Toast.makeText(this, "Could not keep access to this photo", Toast.LENGTH_LONG).show();
        }
    }

    private void composePost(Uri photo) {
        EditText input = new EditText(this);
        input.setHint(photo == null ? "What's on your mind?" : "Add a caption (optional)");
        input.setMinLines(3);
        input.setFilters(new InputFilter[] { new InputFilter.LengthFilter(280) });
        AlertDialog dialog = new AlertDialog.Builder(this)
            .setTitle(photo == null ? "Write a local post" : "Post photo on this phone")
            .setView(input)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Post", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener(v -> {
                String body = input.getText().toString().trim();
                if (body.isEmpty() && photo == null) { input.setError("Write something first"); return; }
                JSONArray previous = savedPosts();
                JSONArray next = new JSONArray();
                JSONObject post = new JSONObject();
                try {
                    post.put("text", body);
                    if (photo != null) post.put("photo", photo.toString());
                } catch (Exception error) { return; }
                next.put(post);
                for (int i = 0; i < Math.min(previous.length(), 49); i++) next.put(previous.opt(i));
                data.edit().putString("posts", next.toString()).apply();
                dialog.dismiss();
                showPosts();
            }));
        dialog.show();
    }

    private void showPosts() {
        posts.removeAllViews();
        JSONArray list = savedPosts();
        if (list.length() == 0) {
            TextView empty = new TextView(this);
            empty.setText("No posts yet. Write your first post above.");
            empty.setTextColor(getColor(R.color.muted));
            empty.setPadding(12, 24, 12, 24);
            posts.addView(empty);
            return;
        }
        for (int i = 0; i < list.length(); i++) {
            final int position = i;
            JSONObject post = list.optJSONObject(i);
            String body = post == null ? list.optString(i) : post.optString("text");
            String photo = post == null ? "" : post.optString("photo");
            LinearLayout card = new LinearLayout(this);
            card.setOrientation(LinearLayout.VERTICAL);
            card.setPadding(20, 20, 20, 20);
            card.setBackgroundColor(getColor(R.color.surface));
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
            params.topMargin = 12;
            posts.addView(card, params);
            if (!photo.isEmpty()) {
                ImageView image = new ImageView(this);
                image.setAdjustViewBounds(true);
                image.setMaxHeight((int)(360 * getResources().getDisplayMetrics().density));
                image.setScaleType(ImageView.ScaleType.CENTER_CROP);
                try { image.setImageURI(Uri.parse(photo)); }
                catch (Exception ignored) { image.setImageResource(R.drawable.apno_mark); }
                card.addView(image, new LinearLayout.LayoutParams(-1, -2));
            }
            if (!body.isEmpty()) {
            TextView row = new TextView(this);
            row.setText(body);
            row.setTextColor(Color.WHITE);
            row.setTextSize(17);
            row.setPadding(0, 12, 0, 8);
            card.addView(row);
            }
            TextView like = new TextView(this);
            boolean liked = post != null && post.optBoolean("liked", false);
            like.setText(liked ? "♥ Liked" : "♡ Like");
            like.setTextColor(getColor(R.color.accent));
            like.setTextSize(16);
            like.setPadding(0, 16, 0, 8);
            card.addView(like);
            like.setOnClickListener(v -> toggleLike(position));
            JSONArray comments = post == null ? null : post.optJSONArray("comments");
            TextView commentButton = new TextView(this);
            int count = comments == null ? 0 : comments.length();
            commentButton.setText("Comments (" + count + ")  ›");
            commentButton.setTextColor(Color.WHITE);
            commentButton.setTextSize(16);
            commentButton.setPadding(0, 12, 0, 12);
            card.addView(commentButton);
            commentButton.setOnClickListener(v -> showComments(position));
            card.setOnLongClickListener(v -> {
                new AlertDialog.Builder(this).setMessage("Delete this local post?")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Delete", (d, which) -> deletePost(position)).show();
                return true;
            });
        }
    }

    private void deletePost(int position) {
        JSONArray previous = savedPosts();
        JSONArray next = new JSONArray();
        for (int i = 0; i < previous.length(); i++)
            if (i != position) next.put(previous.opt(i));
        data.edit().putString("posts", next.toString()).apply();
        showPosts();
    }

    private void toggleLike(int position) {
        JSONArray previous = savedPosts();
        if (position < 0 || position >= previous.length()) return;
        JSONObject post = previous.optJSONObject(position);
        if (post == null) {
            post = new JSONObject();
            try { post.put("text", previous.optString(position)); }
            catch (Exception ignored) { return; }
        }
        try { post.put("liked", !post.optBoolean("liked", false)); }
        catch (Exception ignored) { return; }
        JSONArray next = new JSONArray();
        for (int i = 0; i < previous.length(); i++) next.put(i == position ? post : previous.opt(i));
        data.edit().putString("posts", next.toString()).apply();
        showPosts();
    }

    private void showComments(int position) {
        JSONArray list = savedPosts();
        JSONObject post = list.optJSONObject(position);
        if (post == null) return;
        JSONArray comments = post.optJSONArray("comments");
        StringBuilder message = new StringBuilder();
        if (comments == null || comments.length() == 0) message.append("No comments yet.");
        else for (int i = 0; i < comments.length(); i++)
            message.append("• ").append(comments.optString(i)).append("\n\n");
        new AlertDialog.Builder(this).setTitle("Local comments")
            .setMessage(message.toString().trim())
            .setNegativeButton("Close", null)
            .setPositiveButton("Add comment", (dialog, which) -> addComment(position)).show();
    }

    private void addComment(int position) {
        EditText input = new EditText(this);
        input.setHint("Write a comment");
        input.setFilters(new InputFilter[] { new InputFilter.LengthFilter(280) });
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Add local comment")
            .setView(input).setNegativeButton("Cancel", null)
            .setPositiveButton("Save", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener(v -> {
                String value = input.getText().toString().trim();
                if (value.isEmpty()) { input.setError("Write a comment first"); return; }
                JSONArray list = savedPosts();
                JSONObject post = list.optJSONObject(position);
                if (post == null) { dialog.dismiss(); return; }
                JSONArray comments = post.optJSONArray("comments");
                if (comments == null) comments = new JSONArray();
                if (comments.length() >= 50) {
                    input.setError("Maximum 50 comments per post"); return;
                }
                comments.put(value);
                try { post.put("comments", comments); }
                catch (Exception error) { return; }
                data.edit().putString("posts", list.toString()).apply();
                dialog.dismiss();
                showPosts();
            }));
        dialog.show();
    }

    private JSONArray savedRooms() {
        try { return new JSONArray(data.getString("rooms", "[]")); }
        catch (Exception ignored) { return new JSONArray(); }
    }

    private void createRoom() {
        EditText name = new EditText(this);
        name.setSingleLine(true);
        name.setHint("Room name");
        name.setFilters(new InputFilter[] { new InputFilter.LengthFilter(40) });
        AlertDialog dialog = new AlertDialog.Builder(this)
            .setTitle("Create a local room")
            .setView(name)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Create", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener(v -> {
                String title = name.getText().toString().trim();
                if (title.isEmpty()) { name.setError("Enter a room name"); return; }
                JSONArray list = savedRooms();
                list.put(title);
                data.edit().putString("rooms", list.toString()).apply();
                dialog.dismiss();
                showRooms();
                openRoom(title);
            }));
        dialog.show();
    }

    private void openRoom(String title) {
        Intent intent = new Intent(this, RoomActivity.class);
        intent.putExtra("room_name", title);
        startActivity(intent);
    }

    private void showRooms() {
        rooms.removeAllViews();
        JSONArray list = savedRooms();
        if (list.length() == 0) {
            TextView empty = new TextView(this);
            empty.setText("No rooms yet. Create your first room above.");
            empty.setTextColor(getColor(R.color.muted));
            empty.setTextSize(16);
            empty.setPadding(12, 24, 12, 24);
            rooms.addView(empty);
            return;
        }
        for (int i = list.length() - 1; i >= 0; i--) {
            final int position = i;
            final String title = list.optString(i);
            TextView row = new TextView(this);
            row.setText("🎙  " + title + "    ›");
            row.setTextColor(Color.WHITE);
            row.setTextSize(18);
            row.setPadding(20, 28, 20, 28);
            row.setBackgroundColor(getColor(R.color.surface));
            LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(-1, -2);
            params.bottomMargin = 12;
            rooms.addView(row, params);
            row.setOnClickListener(v -> openRoom(title));
            row.setOnLongClickListener(v -> {
                new AlertDialog.Builder(this).setMessage("Delete this local room?")
                    .setNegativeButton("Cancel", null)
                    .setPositiveButton("Delete", (d, which) -> deleteRoom(position)).show();
                return true;
            });
        }
    }

    private void deleteRoom(int position) {
        JSONArray previous = savedRooms();
        JSONArray next = new JSONArray();
        for (int i = 0; i < previous.length(); i++) {
            if (i != position) next.put(previous.opt(i));
        }
        data.edit().putString("rooms", next.toString()).apply();
        showRooms();
        Toast.makeText(this, "Room removed from this phone", Toast.LENGTH_SHORT).show();
    }
}
