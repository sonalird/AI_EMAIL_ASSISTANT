import argparse
import os
from dotenv import load_dotenv
from .graph import app, EmailState

load_dotenv()

def run_email_assistant(text: str):
    init = EmailState(raw=text)
    final = app.invoke(init)
    return {
        "subject": final.draft_subject,
        "body": final.personalized_body or final.draft_body,
        "route": final.route,
    }


def parse_args():
    p = argparse.ArgumentParser(description="Multi-agent Email Assistant")
    p.add_argument("text", help="Input description of the email to generate")
    return p.parse_args()


def main():
    args = parse_args()
    result = run_email_assistant(args.text)
    print("Subject:", result["subject"]) 
    print("\n" + (result["body"] or "")) 
    print("\nRoute:", result["route"]) 


if __name__ == "__main__":
    main()
