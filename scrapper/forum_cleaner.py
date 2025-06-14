import json

with open("forum_scrap.json", "r") as f:
    forum_data = json.load(f)

full_posts = []
for topic in forum_data:
    posts = topic['posts']
    post_convo = []
    for post in posts:
        post_convo.append(post['text'])
    full_text = f"Title: {topic['title']} \n\n"+"\n\n".join(post_convo)
    full_posts.append({
        "topic":topic['title'],
        "url":fr"https://discourse.onlinedegree.iitm.ac.in/t/{topic['slug']}/{topic['topic_id']}",
        "text":full_text
    })
    with open("forum_clean.json", "w") as f:
        json.dump(full_posts, f, indent=2)
