# Smart Food Waste Management System

A beginner-friendly Streamlit web application that combines:
- AI food image classification using a pretrained Hugging Face model
- Surplus food donation listing and search
- SQLite storage for donation records
- Donation status management
- Dashboard summaries

## Requirements
- Windows, macOS, or Linux
- Python 3.10 or 3.11 recommended
- Internet connection for installing packages and downloading the AI model the first time

## Setup on Windows

1. Install Python 3.10 or 3.11 from https://www.python.org/downloads/
   During installation, select **Add Python to PATH**.
2. Extract this ZIP file.
3. Open Command Prompt in the extracted `ai_food_waste_management` folder.
4. Create a virtual environment:

   ```bat
   py -m venv .venv
   ```

5. Activate it:

   ```bat
   .venv\Scripts\activate
   ```

6. Install dependencies:

   ```bat
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

   PyTorch installation can vary by computer. If `pip install -r requirements.txt` fails on torch, follow the official selector at https://pytorch.org/get-started/locally/ and then run `pip install streamlit pillow transformers`.

7. Start the app:

   ```bat
   streamlit run app.py
   ```

8. Your browser should open the app. If it does not, open the local URL printed in the terminal (usually http://localhost:8501).

## How to use it

1. Open **AI Food Classifier**, upload a JPG/PNG image, and view the top predictions.
2. Open **Add Donation** and enter donor, contact, food, quantity, location, and deadline.
3. Open **Available Food** to search listings.
4. Open **Manage Donations** to mark a donation Reserved, Collected, or Cancelled.
5. The `food_donations.db` SQLite file is created automatically beside `app.py`.

## Notes and limitations

- The first AI classification may take time because the pretrained model must be downloaded.
- The classifier can make mistakes. Review its prediction before saving a donation.
- Image classification does not determine freshness, contamination, allergens, or whether food is safe to eat.
- This is a student prototype. It does not send real SMS/email alerts, verify user identities, or connect donors to charities automatically.
- Do not use real private contact details in a public demo.
