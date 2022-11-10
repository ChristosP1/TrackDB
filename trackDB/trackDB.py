import xml.etree.ElementTree as ET
import sqlite3

conn = sqlite3.connect('trackdb.sqlite')
cur = conn.cursor()

# Make some fresh tables using executescript()
cur.executescript('''
DROP TABLE IF EXISTS Artist;
DROP TABLE IF EXISTS Album;
DROP TABLE IF EXISTS Track;
DROP TABLE IF EXISTS Genre;

CREATE TABLE Artist (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name    TEXT UNIQUE
);

CREATE TABLE Genre (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    name    TEXT UNIQUE
);

CREATE TABLE Album (
    id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
    artist_id  INTEGER,
    title   TEXT UNIQUE
);

CREATE TABLE Track (
    id  INTEGER NOT NULL PRIMARY KEY
        AUTOINCREMENT UNIQUE,
    title TEXT  UNIQUE,
    album_id  INTEGER,
    genre_id  INTEGER,
    len INTEGER, rating INTEGER, count INTEGER
);''')

#Asking the user for the exported XML file
fname = input('Enter file name: ')


def lookup(ent, key):
    found = False
    for child in ent:
        if found : return child.text
        if child.tag == 'key' and child.text == key :
            found = True
    return None

#Transforming the data in a more readable type for the pc (Element Tree)
#and breaking it into elements with 3 <dict> depth (one song each)
stuff = ET.parse(fname)
all = stuff.findall('dict/dict/dict')
print('Dictionaries found:', len(all))

i=0

#For every entry(song) check if it has the basic info and add it
for entry in all:
    if ( lookup(entry, 'Track ID') is None ) : continue

    #Extracting basic data to add to the DB
    name = lookup(entry, 'Name')
    artist = lookup(entry, 'Artist')
    album = lookup(entry, 'Album')
    genre = lookup(entry, 'Genre')
    count = lookup(entry, 'Play Count')
    rating = lookup(entry, 'Rating')
    length = lookup(entry, 'Total Time')

    if name is None or artist is None or album is None or genre is None :
        continue

    #for debuging
    #print(name, artist, album,genre, count, rating, length)

    #Insert only if it doesn't exist in the DB and fetch its id
    cur.execute('''INSERT OR IGNORE INTO Artist (name)
        VALUES ( ? )''', ( artist, ) )
    cur.execute('SELECT id FROM Artist WHERE name = ? ', (artist, ))
    artist_id = cur.fetchone()[0]

    cur.execute('''INSERT OR IGNORE INTO Album (title, artist_id )
        VALUES ( ?, ? )''', ( album, artist_id ) )
    cur.execute('SELECT id FROM Album WHERE title = ? ', (album, ))
    album_id = cur.fetchone()[0]

    cur.execute('''INSERT OR IGNORE INTO Genre (name)
        VALUES ( ? )''', ( genre, ) )
    cur.execute('SELECT id FROM Genre WHERE name = ? ', (genre, ))
    genre_id = cur.fetchone()[0]

    #We use the previous ids to save Track's data in a more coded way
    cur.execute('''INSERT OR REPLACE INTO Track
        (title, album_id, len, rating, count, genre_id)
        VALUES ( ?, ?, ?, ?, ?, ? )''',
        ( name, album_id, length, rating, count, genre_id ) )

    #Commit every 5 tracks
    if i%5 == 0:
        conn.commit()
