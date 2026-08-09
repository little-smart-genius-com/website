import json
f1 = 'data/archive_posts/fine-motor-busy-book-pages-for-toddlers-printable-1779274941.json'
with open(f1, 'r', encoding='utf-8') as f:
    d = json.load(f)
c = d['content']
idx = c.find('fine-motor-busy-book-pages-for-toddlers-printable-best-resources-img4-thumb')
print("IDX 1:", idx)
end_idx = c.find('loading=', idx)
print("END IDX 1:", end_idx)

f2 = 'data/archive_posts/spot-the-difference-activities-sharpen-focus-in-6-year-olds-1777027975.json'
with open(f2, 'r', encoding='utf-8') as f:
    d2 = json.load(f)
c2 = d2['content']
idx2 = c2.find('how-spot-the-difference-activities-sharpen-focus-in-6-year-olds-various')
print("IDX 2:", idx2)
end_idx2 = c2.find('loading=', idx2)
print("END IDX 2:", end_idx2)
