import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup

BASE_URL = "https://discourse.onlinedegree.iitm.ac.in/c/courses/tds-kb/34.json"
START_TIME = datetime(2025,1,1)
END_TIME = datetime(2025,4,14)
cookies = {
    "_forum_session":"fcF6nV3SkAC0K0Z2dIgjZjzRHkD7bz1RTcRtWXe5HnEhp%2BAa5oLT6Kv8azkygCfhgsFdSafLfokdcbsi5JTJ8fLLZwfI%2FStYHyjdiWOIAT55KrAAlIscICNd3uo8oYEZLP5jCkkLTvuooVFoeBzlyoAx7qbvwZrUz%2BFN5NjR9uX7XAuoAHofe3mqu8e7zU7a0bHi7Zbiyw05SdYBM3oYWlVojl1mSrKBIagyJkArRWXtONH4SsafoDnuoFKLh31MaLbkohsNYKuOWjZXdxAaXONlTLEU1HuWJbtU0vopaMQ9ldTE78S6Ux%2FV6mnKNt%2FfIisFYwnlpdYJb7g5w%2B2BRzs4mbapJD8r93%2B3epWvY0DgRUA8FI7425FAfpCq6w%3D%3D--PbtFdDiXWvb0taQR--Qg4NvP62snpkhSAs%2FM5Jtw%3D%3D",
    "_t":"%2BZo9EuWZNsR6UMOOmMmED6UwKr5GtthlC3SfZj5kKbWvkqqrsXilb1dxIBaOUYBkrWsBfMWFtvKvSkJH8fGq8XewbSIKLXdCKy1xLTpe0FI74JTyK6NwFnY9X%2BU0MtKmesBAe%2BV6Bj04wiX0ZUzCU%2F%2FP9Re0Gje30TdCeS80B7z7pSm2URB6UTM2PAdq%2FGZhSxdV5aorLwxa7IS8ix6lQ%2FKVymYq6mMeg%2BlripRPlISkN8WHQsKklnCBOajbJ8oWQxjd2TLZMFxLX8gghfsDrRFL4sj5lvAahm7WJNA21aoze4JfNhOp68lLgqsMf5Mz--gzsfEPQbsfSQvSVe--Km13M7SBZqIaUSGcsREIag%3D%3D"
}

def clean_cooked(cooked):
    return BeautifulSoup(cooked, "html.parser").get_text(separator='\n').strip()

def compareDate(start_time, end_time, date_str):
    created = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    created = created.replace(tzinfo=None) 
    return start_time <= created <= end_time

def get_title_post(out_dir):
    page = 0
    filtered_topics = []
    flag = True
    while(flag):
        try:
            url = f"{BASE_URL}?page={page}"
            req = requests.get(url, cookies=cookies)
            topics = req.json().get("topic_list", {}).get("topics", [])
            if not topics:
                break;
        except Exception as e:
            print(f"Failed to fetch topic list on page {page}: {e}")
            break
        
        print(f"Page: {page}")
        for topic in topics:
            if not compareDate(START_TIME, datetime.now(), topic['last_posted_at']):
                flag = False
                break
            try:
                post_url = fr"https://discourse.onlinedegree.iitm.ac.in/t/{topic['slug']}/{topic['id']}.json"
                in_res = requests.get(url=post_url, cookies=cookies)
                posts_in_topic= in_res.json().get('post_stream', {}).get("posts", [])
                
                filtered_posts = []
                
                for post in posts_in_topic:
                    try:
                        if compareDate(START_TIME, END_TIME, post['created_at']):
                            if post['cooked']:
                                filtered_posts.append({
                                    'id':post['id'],
                                    'created_at': post['created_at'],
                                    'text':clean_cooked(post['cooked'])
                                })
                    except Exception as post_err:
                        print(f"⚠️ Post parse error: {post_err}")
                        continue
                if filtered_posts:
                    filtered_topics.append({
                        'topic_id':topic['id'],
                        'title':topic['title'],
                        'slug':topic['slug'],
                        'created_at':topic['created_at'],
                        'last_posted_at':topic['last_posted_at'],
                        'posts':filtered_posts
                    })
                    print(json.dumps(filtered_topics, indent=2))
                    with open(out_dir, "w", encoding="utf-8") as f:
                        json.dump(filtered_topics, f, indent=2, ensure_ascii=False)
                    
                    time.sleep(1)
            except Exception as topic_err:
                print(f"Error processing topic {topic['id']}: {topic_err}")
                continue
        page+=1
    
    return filtered_topics
if __name__ == "__main__":
    get_title_post("forum_scrap.json")
