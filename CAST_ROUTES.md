# Cast Container Routes

## Overview

Script.skinvariables now provides routes to populate containers with cast information from Kodi's local database. This addresses issue #1553 by enabling cast display when using `call_auto` with `add_dbid`.

## Available Routes

### Movie Cast
Retrieves cast information for a movie by its database ID.

**Route:** `get_dbitem_movie_cast`

**URL Format:**
```
plugin://script.skinvariables/?info=get_dbitem_movie_cast&dbid=<movieid>
```

**Example:**
```xml
<onclick>Container(50).Update(plugin://script.skinvariables/?info=get_dbitem_movie_cast&dbid=$INFO[ListItem.DBID])</onclick>
```

### TV Show Cast
Retrieves cast information for a TV show by its database ID.

**Route:** `get_dbitem_tvshow_cast`

**URL Format:**
```
plugin://script.skinvariables/?info=get_dbitem_tvshow_cast&dbid=<tvshowid>
```

**Example:**
```xml
<onclick>Container(50).Update(plugin://script.skinvariables/?info=get_dbitem_tvshow_cast&dbid=$INFO[ListItem.DBID])</onclick>
```

### Episode Cast
Retrieves cast information for an episode by its database ID.

**Route:** `get_dbitem_episode_cast`

**URL Format:**
```
plugin://script.skinvariables/?info=get_dbitem_episode_cast&dbid=<episodeid>
```

**Example:**
```xml
<onclick>Container(50).Update(plugin://script.skinvariables/?info=get_dbitem_episode_cast&dbid=$INFO[ListItem.DBID])</onclick>
```

## Cast ListItem Properties

Each cast member in the container has the following properties:

| Property | Description | Example |
|----------|-------------|---------|
| `Label` | Actor name | "Robert Downey Jr." |
| `Label2` | Character/Role name | "Tony Stark" |
| `Art(thumb)` | Actor thumbnail image | "image://http%3a%2f%2f..." |
| `Property(name)` | Actor name (property) | "Robert Downey Jr." |
| `Property(role)` | Character name (property) | "Tony Stark" |
| `Property(order)` | Cast order | "0" |
| `Property(index)` | Zero-based index | "0" |
| `Property(thumbnail)` | Actor thumbnail URL | "image://http%3a%2f%2f..." |

## Skin XML Examples

### Basic Cast List

```xml
<control type="list" id="50">
    <left>100</left>
    <top>200</top>
    <width>1720</width>
    <height>600</height>
    <onleft>9000</onleft>
    <onright>9000</onright>
    <onup>50</onup>
    <ondown>50</ondown>
    <orientation>horizontal</orientation>
    <itemlayout width="200" height="300">
        <control type="image">
            <left>10</left>
            <top>10</top>
            <width>180</width>
            <height>270</height>
            <texture>$INFO[ListItem.Art(thumb)]</texture>
            <aspectratio>scale</aspectratio>
        </control>
        <control type="label">
            <left>10</left>
            <top>285</top>
            <width>180</width>
            <height>30</height>
            <label>$INFO[ListItem.Label]</label>
            <font>font12</font>
            <textcolor>white</textcolor>
            <align>center</align>
        </control>
        <control type="label">
            <left>10</left>
            <top>315</top>
            <width>180</width>
            <height>25</height>
            <label>$INFO[ListItem.Label2]</label>
            <font>font10</font>
            <textcolor>grey</textcolor>
            <align>center</align>
        </control>
    </itemlayout>
    <focusedlayout width="200" height="300">
        <control type="image">
            <left>10</left>
            <top>10</top>
            <width>180</width>
            <height>270</height>
            <texture>$INFO[ListItem.Art(thumb)]</texture>
            <aspectratio>scale</aspectratio>
            <bordertexture border="5">colors/white.png</bordertexture>
            <bordersize>5</bordersize>
        </control>
        <control type="label">
            <left>10</left>
            <top>285</top>
            <width>180</width>
            <height>30</height>
            <label>$INFO[ListItem.Label]</label>
            <font>font12_title</font>
            <textcolor>white</textcolor>
            <align>center</align>
        </control>
        <control type="label">
            <left>10</left>
            <top>315</top>
            <width>180</width>
            <height>25</height>
            <label>$INFO[ListItem.Label2]</label>
            <font>font10</font>
            <textcolor>grey</textcolor>
            <align>center</align>
        </control>
    </focusedlayout>
</control>
```

### Updating Cast Container on Info Dialog Open

```xml
<!-- In DialogVideoInfo.xml -->
<onload>Container(50).Update(plugin://script.skinvariables/?info=get_dbitem_$INFO[ListItem.DBType]_cast&dbid=$INFO[ListItem.DBID])</onload>
```

### Conditional Cast Display

```xml
<!-- Show cast list only when container has items -->
<control type="group">
    <visible>Integer.IsGreater(Container(50).NumItems,0)</visible>
    <control type="label>
        <label>Cast</label>
    </control>
    <control type="list" id="50">
        <!-- cast list control -->
    </control>
</control>
```

### Accessing Specific Cast Members

```xml
<!-- First cast member -->
<control type="label>
    <label>$INFO[Container(50).ListItem(0).Label]</label>
</control>

<!-- Second cast member -->
<control type="label>
    <label>$INFO[Container(50).ListItem(1).Label]</label>
</control>

<!-- Number of cast members -->
<control type="label>
    <label>Cast: $INFO[Container(50).NumItems]</label>
</control>
```

## Integration with TMDb Helper

When using with plugin.video.themoviedb.helper's `call_auto` feature:

```xml
<onclick>RunScript(plugin.video.themoviedb.helper,add_dbid=$INFO[ListItem.DBID],tmdb_type=movie,call_auto=1190)</onclick>
```

The cast container will now be properly populated when the info dialog opens, thanks to the new cast routes.

## Requirements

- **script.skinvariables:** v2.1.35+
- **script.module.jurialmunkey:** v0.2.30+
- **Kodi Version:** 19+ (Nexus)

## Notes

- Cast data is retrieved from Kodi's local database
- No external API calls are made
- Cast members are ordered by their billing order (as scraped)
- If a movie/show has no cast data, the container will be empty
- Thumbnails are automatically loaded from Kodi's artwork cache

## Troubleshooting

**Container not populating:**
- Verify the container ID (50 in examples) exists in your skin XML
- Check that the media item has cast data in the Kodi library
- Ensure script.module.jurialmunkey is updated to v0.2.30 or higher

**Thumbnails not showing:**
- Verify artwork scrapers are enabled in Kodi settings
- Check that Kodi's artwork downloader has run
- Ensure sufficient cache space for artwork

**Wrong cast information:**
- Verify the correct `info` parameter is used (movie_cast vs tvshow_cast vs episode_cast)
- Check that the correct DBID is being passed
- Rescrape the media item if data appears incorrect

## Related Issues

- [Issue #1553](https://github.com/jurialmunkey/plugin.video.themoviedb.helper/issues/1553) - Empty Cast Container with call_auto and add_dbid

## Changelog

### v2.1.35
- Added `get_dbitem_movie_cast` route
- Added `get_dbitem_tvshow_cast` route  
- Added `get_dbitem_episode_cast` route
- Updated dependency on script.module.jurialmunkey to v0.2.30
