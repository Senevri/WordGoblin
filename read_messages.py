import yaml
from pathlib import Path

print ("start")
glob =  Path(Path.cwd() / "repl_messages/").glob("*.yaml")
print(glob)
files = list(glob)
print(files)

messages = []
for file in files:
    with open(file, "r", encoding="utf-8") as f:
        message = yaml.safe_load(f)
        messages.extend(message)

target = Path(Path.cwd() / "readable_messages.yaml")
messagestr = []
for message in messages:
    if content:= message.get("content"):
        messagestr.append(f"{message['role']}:\n{message['content']}\n\n")
with open(target, "w", encoding="utf-8") as f:
    f.writelines(messagestr)
print ("done")
