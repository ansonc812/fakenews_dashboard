#!/usr/bin/env python3
"""
Quick script to import PolitiFact data specifically
"""

import psycopg2
import csv
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/fakenewsnet')

def import_politifact():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # Ensure politifact source exists
    cur.execute("""
        INSERT INTO news_source (source_name, source_url, credibility_rating)
        VALUES ('politifact', 'https://politifact.com', 0.90)
        ON CONFLICT (source_name) DO UPDATE SET
        source_url = EXCLUDED.source_url,
        credibility_rating = EXCLUDED.credibility_rating
        RETURNING source_id
    """)
    source_id = cur.fetchone()[0]
    
    # Get politics category
    cur.execute("SELECT category_id FROM news_category WHERE category_name = 'politics'")
    politics_category_id = cur.fetchone()[0]
    
    files = [
        ('politifact_fake.csv', 'fake'),
        ('politifact_real.csv', 'real')
    ]
    
    base_path = "/home/ansonc812/Documents/git/repos/fakenews_dashboard/project 1+2 deliverables/fakenewsnet/FakeNewsNet-master/dataset"
    
    total_imported = 0
    
    for filename, label in files:
        filepath = os.path.join(base_path, filename)
        print(f"Processing {filename}...")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            
            for i, row in enumerate(reader):
                try:
                    article_id = f"politifact_{total_imported + 1}"
                    title = row.get('title', '')[:500]
                    url = row.get('news_url', row.get('url', ''))[:500]
                    
                    if not title or not url:
                        continue
                    
                    cur.execute("""
                        INSERT INTO news_article (article_id, source_id, title, url, label, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (article_id) DO NOTHING
                    """, (article_id, source_id, title, url, label, datetime.now()))
                    
                    # Insert content
                    content = row.get('content', row.get('text', ''))
                    if content:
                        cur.execute("""
                            INSERT INTO news_content (article_id, text)
                            VALUES (%s, %s)
                            ON CONFLICT (article_id) DO NOTHING
                        """, (article_id, content))
                    
                    # Link to politics category
                    cur.execute("""
                        INSERT INTO article_category (article_id, category_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING
                    """, (article_id, politics_category_id))
                    
                    total_imported += 1
                    
                    if total_imported % 1000 == 0:
                        print(f"  Imported {total_imported} articles...")
                        conn.commit()
                
                except Exception as e:
                    print(f"Error importing row {i}: {e}")
                    continue
        
        conn.commit()
        print(f"Completed {filename}")
    
    cur.close()
    conn.close()
    print(f"\nTotal PolitiFact articles imported: {total_imported}")

if __name__ == "__main__":
    import_politifact()