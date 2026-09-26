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
import android.widget.ScrollView;
import android.text.InputFilter;
import android.text.TextWatcher;
import android.text.Editable;
import java.util.Locale;
import org.json.JSONArray;
import org.json.JSONObject;

public class HomeActivity extends Activity {
    private static final int PICK_POST_PHOTO = 42;
    private static final int PICK_POST_VIDEO = 43;
    private SharedPreferences data;
    private LinearLayout rooms;
    private LinearLayout posts;
    private LinearLayout savedPostsView;
    private EditText searchPosts;
    private LinearLayout discoverRooms;
    private String selectedCategory = "Hot";
    private static final String[] CATEGORIES = { "Hot", "Event", "Date", "Music", "Game" };

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(getColor(R.color.navy));
        getWindow().setNavigationBarColor(getColor(R.color.navy));
        setContentView(R.layout.activity_home);
        data = getSharedPreferences("apno_preview", MODE_PRIVATE);
        rooms = findViewById(R.id.rooms);
        posts = findViewById(R.id.posts);
        savedPostsView = findViewById(R.id.saved_posts);
        discoverRooms = findViewById(R.id.discover_rooms);
        setupNavigation();
        showCategories();
        searchPosts = findViewById(R.id.search_posts);
        searchPosts.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int start, int count, int after) { }
            @Override public void onTextChanged(CharSequence s, int start, int before, int count) { showPosts(); }
            @Override public void afterTextChanged(Editable s) { }
        });
        findViewById(R.id.create_post).setOnClickListener(v -> createPost());
        findViewById(R.id.create_photo_post).setOnClickListener(v -> pickPostPhoto());
        findViewById(R.id.create_video_post).setOnClickListener(v -> pickPostVideo());
        findViewById(R.id.create_room).setOnClickListener(v -> createRoom());
        findViewById(R.id.top_search).setOnClickListener(v -> {
            selectTab(R.id.party_panel, R.id.tab_party, "Apno");
            searchPosts.requestFocus();
            ((ScrollView) findViewById(R.id.content_scroll)).smoothScrollTo(0, searchPosts.getTop());
        });
        showRooms();
        showPosts();
    }

    private void setupNavigation() {
        findViewById(R.id.tab_party).setOnClickListener(v -> selectTab(R.id.party_panel, R.id.tab_party, "Apno"));
        findViewById(R.id.tab_game).setOnClickListener(v -> selectTab(R.id.game_panel, R.id.tab_game, "Game"));
        findViewById(R.id.tab_discover).setOnClickListener(v -> {
            showDiscoverRooms();
            selectTab(R.id.discover_panel, R.id.tab_discover, "Discover");
        });
        findViewById(R.id.tab_messages).setOnClickListener(v -> selectTab(R.id.messages_panel, R.id.tab_messages, "Messages"));
        findViewById(R.id.tab_me).setOnClickListener(v -> startActivity(new Intent(this, ProfileActivity.class)));
        selectTab(R.id.party_panel, R.id.tab_party, "Apno");
    }

    private void selectTab(int panelId, int tabId, String title) {
        int[] panels = { R.id.party_panel, R.id.game_panel, R.id.discover_panel, R.id.messages_panel };
        int[] tabs = { R.id.tab_party, R.id.tab_game, R.id.tab_discover, R.id.tab_messages, R.id.tab_me };
        for (int id : panels) findViewById(id).setVisibility(id == panelId ? View.VISIBLE : View.GONE);
        for (int id : tabs) ((TextView) findViewById(id)).setTextColor(getColor(id == tabId ? R.color.yellow : R.color.muted));
        ((TextView) findViewById(R.id.section_title)).setText(title);
        ((ScrollView) findViewById(R.id.content_scroll)).scrollTo(0, 0);
    }

    private void showCategories() {
        LinearLayout bar = findViewById(R.id.categories);
        bar.removeAllViews();
        for (String category : CATEGORIES) {
            TextView chip = new TextView(this);
            chip.setText(category);
            chip.setTextSize(16);
            chip.setGravity(android.view.Gravity.CENTER);
            chip.setPadding(28, 16, 28, 16);
            chip.setTextColor(getColor(category.equals(selectedCategory) ? R.color.navy : R.color.white));
            chip.setBackgroundColor(getColor(category.equals(selectedCategory) ? R.color.yellow : R.color.surface));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-2, -2);
            lp.rightMargin = 10;
            bar.addView(chip, lp);
            chip.setOnClickListener(v -> {
                selectedCategory = category;
                showCategories();
                showRooms();
            });
        }
    }

    private JSONArray savedPosts() {
        try { return new JSONArray(data.getString("posts", "[]")); }
        catch (Exception ignored) { return new JSONArray(); }
    }

    private void createPost() {
        composePost(null, false);
    }

    private void pickPostPhoto() {
        pickMedia("image/*", PICK_POST_PHOTO);
    }

    private void pickPostVideo() {
        pickMedia("video/*", PICK_POST_VIDEO);
    }

    private void pickMedia(String type, int requestCode) {
        Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
        intent.setType(type);
        intent.addCategory(Intent.CATEGORY_OPENABLE);
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
        startActivityForResult(intent, requestCode);
    }

    @Override protected void onActivityResult(int requestCode, int resultCode, Intent result) {
        super.onActivityResult(requestCode, resultCode, result);
        if ((requestCode != PICK_POST_PHOTO && requestCode != PICK_POST_VIDEO)
            || resultCode != RESULT_OK || result == null || result.getData() == null) return;
        Uri uri = result.getData();
        try {
            getContentResolver().takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION);
            composePost(uri, requestCode == PICK_POST_VIDEO);
        } catch (SecurityException exception) {
            Toast.makeText(this, "Could not keep access to this media", Toast.LENGTH_LONG).show();
        }
    }

    private void composePost(Uri media, boolean video) {
        EditText input = new EditText(this);
        input.setHint(media == null ? "What's on your mind?" : "Add a caption (optional)");
        input.setMinLines(3);
        input.setFilters(new InputFilter[] { new InputFilter.LengthFilter(280) });
        AlertDialog dialog = new AlertDialog.Builder(this)
            .setTitle(media == null ? "Write a local post" : video ? "Post video on this phone" : "Post photo on this phone")
            .setView(input)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Post", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener(v -> {
                String body = input.getText().toString().trim();
                if (body.isEmpty() && media == null) { input.setError("Write something first"); return; }
                JSONArray previous = savedPosts();
                JSONArray next = new JSONArray();
                JSONObject post = new JSONObject();
                try {
                    post.put("text", body);
                    if (media != null) post.put(video ? "video" : "photo", media.toString());
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
        savedPostsView.removeAllViews();
        JSONArray list = savedPosts();
        String query = searchPosts.getText().toString().trim().toLowerCase(Locale.ROOT);
        if (list.length() == 0) {
            TextView empty = new TextView(this);
            empty.setText("No posts yet. Write your first post above.");
            empty.setTextColor(getColor(R.color.muted));
            empty.setPadding(12, 24, 12, 24);
            posts.addView(empty);
            showSavedEmpty();
            return;
        }
        for (int i = 0; i < list.length(); i++) {
            final int position = i;
            JSONObject post = list.optJSONObject(i);
            String body = post == null ? list.optString(i) : post.optString("text");
            String photo = post == null ? "" : post.optString("photo");
            String video = post == null ? "" : post.optString("video");
            if (!query.isEmpty() && !body.toLowerCase(Locale.ROOT).contains(query)) continue;
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
            if (!video.isEmpty()) {
                TextView play = new TextView(this);
                play.setText("▶  Play video");
                play.setTextColor(getColor(R.color.accent));
                play.setTextSize(18);
                play.setPadding(0, 24, 0, 24);
                card.addView(play);
                play.setOnClickListener(v -> {
                    try {
                        Intent open = new Intent(Intent.ACTION_VIEW);
                        open.setDataAndType(Uri.parse(video), "video/*");
                        open.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                        startActivity(open);
                    } catch (Exception error) {
                        Toast.makeText(this, "No video player available", Toast.LENGTH_SHORT).show();
                    }
                });
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
            TextView bookmark = new TextView(this);
            bookmark.setText(post != null && post.optBoolean("saved") ? "★ Saved" : "☆ Save");
            bookmark.setTextColor(getColor(R.color.accent));
            bookmark.setTextSize(16);
            bookmark.setPadding(0, 12, 0, 12);
            card.addView(bookmark);
            bookmark.setOnClickListener(v -> toggleSaved(position));
            TextView share = new TextView(this);
            share.setText("↗ Share");
            share.setTextColor(Color.WHITE);
            share.setTextSize(16);
            share.setPadding(0, 12, 0, 12);
            card.addView(share);
            share.setOnClickListener(v -> sharePost(position));
            if (post != null && post.optBoolean("saved")) {
                TextView saved = new TextView(this);
                saved.setText("★  " + (body.isEmpty() ? (!video.isEmpty() ? "Video post" : "Photo post") : body));
                saved.setMaxLines(2);
                saved.setTextColor(Color.WHITE);
                saved.setTextSize(16);
                saved.setPadding(20, 18, 20, 18);
                saved.setBackgroundColor(getColor(R.color.surface));
                LinearLayout.LayoutParams savedParams = new LinearLayout.LayoutParams(-1, -2);
                savedParams.topMargin = 10;
                savedPostsView.addView(saved, savedParams);
            }
            card.setOnLongClickListener(v -> {
                new AlertDialog.Builder(this).setTitle("Post options")
                    .setItems(new String[] { "Edit caption", "Delete post" }, (d, which) -> {
                        if (which == 0) editPost(position);
                        else new AlertDialog.Builder(this).setMessage("Delete this local post?")
                            .setNegativeButton("Cancel", null)
                            .setPositiveButton("Delete", (confirm, choice) -> deletePost(position)).show();
                    }).show();
                return true;
            });
        }
        if (posts.getChildCount() == 0) {
            TextView empty = new TextView(this);
            empty.setText("No posts match your search.");
            empty.setTextColor(getColor(R.color.muted));
            empty.setPadding(12, 24, 12, 24);
            posts.addView(empty);
        }
        if (savedPostsView.getChildCount() == 0) showSavedEmpty();
    }

    private void showSavedEmpty() {
        TextView empty = new TextView(this);
        empty.setText("Save a post to see it here.");
        empty.setTextColor(getColor(R.color.muted));
        empty.setPadding(12, 24, 12, 24);
        savedPostsView.addView(empty);
    }

    private void toggleSaved(int position) {
        JSONArray list = savedPosts();
        JSONObject post = list.optJSONObject(position);
        if (post == null) {
            post = new JSONObject();
            try { post.put("text", list.optString(position)); }
            catch (Exception ignored) { return; }
            try { list.put(position, post); }
            catch (Exception ignored) { return; }
        }
        try { post.put("saved", !post.optBoolean("saved")); }
        catch (Exception ignored) { return; }
        data.edit().putString("posts", list.toString()).apply();
        showPosts();
    }

    private void sharePost(int position) {
        JSONObject post = savedPosts().optJSONObject(position);
        if (post == null) return;
        String body = post.optString("text", "");
        String media = post.optString("photo", "");
        if (media.isEmpty()) media = post.optString("video", "");
        Intent share = new Intent(Intent.ACTION_SEND);
        if (media.isEmpty()) {
            share.setType("text/plain");
        } else {
            share.setType(post.has("video") ? "video/*" : "image/*");
            share.putExtra(Intent.EXTRA_STREAM, Uri.parse(media));
            share.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        }
        share.putExtra(Intent.EXTRA_TEXT, body);
        try { startActivity(Intent.createChooser(share, "Share post")); }
        catch (Exception error) { Toast.makeText(this, "No share app available", Toast.LENGTH_SHORT).show(); }
    }

    private void deletePost(int position) {
        JSONArray previous = savedPosts();
        JSONArray next = new JSONArray();
        for (int i = 0; i < previous.length(); i++)
            if (i != position) next.put(previous.opt(i));
        data.edit().putString("posts", next.toString()).apply();
        showPosts();
    }

    private void editPost(int position) {
        JSONArray list = savedPosts();
        JSONObject post = list.optJSONObject(position);
        String original = post == null ? list.optString(position) : post.optString("text");
        EditText input = new EditText(this);
        input.setText(original);
        input.setSelection(input.length());
        input.setFilters(new InputFilter[] { new InputFilter.LengthFilter(280) });
        AlertDialog dialog = new AlertDialog.Builder(this).setTitle("Edit post")
            .setView(input).setNegativeButton("Cancel", null)
            .setPositiveButton("Save", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener(v -> {
                String body = input.getText().toString().trim();
                if (body.isEmpty() && (post == null || (!post.has("photo") && !post.has("video")))) {
                    input.setError("Write something first"); return;
                }
                JSONArray current = savedPosts();
                JSONObject updated = current.optJSONObject(position);
                if (updated == null) updated = new JSONObject();
                try {
                    updated.put("text", body);
                    current.put(position, updated);
                } catch (Exception error) { return; }
                data.edit().putString("posts", current.toString()).apply();
                dialog.dismiss();
                showPosts();
            }));
        dialog.show();
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
        AlertDialog.Builder builder = new AlertDialog.Builder(this).setTitle("Local comments")
            .setMessage(message.toString().trim())
            .setNegativeButton("Close", null)
            .setPositiveButton("Add comment", (dialog, which) -> addComment(position));
        if (comments != null && comments.length() > 0)
            builder.setNeutralButton("Remove comment", (dialog, which) -> chooseCommentToRemove(position));
        builder.show();
    }

    private void chooseCommentToRemove(int position) {
        JSONObject post = savedPosts().optJSONObject(position);
        if (post == null) return;
        JSONArray comments = post.optJSONArray("comments");
        if (comments == null || comments.length() == 0) return;
        String[] items = new String[comments.length()];
        for (int i = 0; i < items.length; i++) items[i] = comments.optString(i);
        new AlertDialog.Builder(this).setTitle("Remove a local comment")
            .setItems(items, (dialog, selected) -> {
                JSONArray current = savedPosts();
                JSONObject currentPost = current.optJSONObject(position);
                if (currentPost == null) return;
                JSONArray old = currentPost.optJSONArray("comments");
                if (old == null || selected >= old.length()) return;
                JSONArray next = new JSONArray();
                for (int i = 0; i < old.length(); i++) if (i != selected) next.put(old.opt(i));
                try { currentPost.put("comments", next); }
                catch (Exception error) { return; }
                data.edit().putString("posts", current.toString()).apply();
                showPosts();
            }).setNegativeButton("Cancel", null).show();
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
        LinearLayout form = new LinearLayout(this);
        form.setOrientation(LinearLayout.VERTICAL);
        form.setPadding(24, 0, 24, 0);
        EditText name = new EditText(this);
        name.setSingleLine(true);
        name.setHint("Room name");
        name.setFilters(new InputFilter[] { new InputFilter.LengthFilter(40) });
        form.addView(name);
        android.widget.Spinner category = new android.widget.Spinner(this);
        category.setAdapter(new android.widget.ArrayAdapter<>(this,
            android.R.layout.simple_spinner_dropdown_item, CATEGORIES));
        form.addView(category);
        AlertDialog dialog = new AlertDialog.Builder(this)
            .setTitle("Create a local room")
            .setView(form)
            .setNegativeButton("Cancel", null)
            .setPositiveButton("Create", null).create();
        dialog.setOnShowListener(ignored -> dialog.getButton(AlertDialog.BUTTON_POSITIVE)
            .setOnClickListener(v -> {
                String title = name.getText().toString().trim();
                if (title.isEmpty()) { name.setError("Enter a room name"); return; }
                JSONArray list = savedRooms();
                JSONObject room = new JSONObject();
                try {
                    room.put("title", title);
                    room.put("category", CATEGORIES[category.getSelectedItemPosition()]);
                } catch (Exception error) { return; }
                list.put(room);
                data.edit().putString("rooms", list.toString()).apply();
                dialog.dismiss();
                showRooms();
                showDiscoverRooms();
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
            JSONObject room = list.optJSONObject(i);
            final String title = room == null ? list.optString(i) : room.optString("title");
            final String category = room == null ? "Hot" : room.optString("category", "Hot");
            if (!selectedCategory.equals("Hot") && !category.equals(selectedCategory)) continue;
            TextView row = new TextView(this);
            row.setText("🎙  " + title + "  ·  " + category + "    ›");
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
        if (rooms.getChildCount() == 0) {
            TextView empty = new TextView(this);
            empty.setText("No " + selectedCategory + " rooms yet. Create one above.");
            empty.setTextColor(getColor(R.color.muted));
            empty.setPadding(12, 24, 12, 24);
            rooms.addView(empty);
        }
    }

    private void showDiscoverRooms() {
        if (discoverRooms == null) return;
        discoverRooms.removeAllViews();
        JSONArray list = savedRooms();
        if (list.length() == 0) {
            TextView empty = new TextView(this);
            empty.setText("No local rooms to discover yet. Create one in Party.");
            empty.setTextColor(getColor(R.color.muted));
            empty.setPadding(12, 28, 12, 28);
            discoverRooms.addView(empty);
            return;
        }
        for (int i = list.length() - 1; i >= 0; i--) {
            JSONObject room = list.optJSONObject(i);
            String title = room == null ? list.optString(i) : room.optString("title");
            String category = room == null ? "Hot" : room.optString("category", "Hot");
            TextView row = new TextView(this);
            row.setText(category + "  ·  " + title + "  ›");
            row.setTextColor(getColor(R.color.white));
            row.setTextSize(18);
            row.setPadding(20, 24, 20, 24);
            row.setBackgroundColor(getColor(R.color.surface));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
            lp.topMargin = 12;
            discoverRooms.addView(row, lp);
            row.setOnClickListener(v -> openRoom(title));
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
        showDiscoverRooms();
        Toast.makeText(this, "Room removed from this phone", Toast.LENGTH_SHORT).show();
    }
}
