# ☁️ S3 Uploader

A sleek, modern desktop application built with Python and Tkinter for effortlessly uploading folders and files to AWS S3. Featuring a compact, dark-themed UI with real-time progress tracking and detailed activity logging.

## ✨ Features

- **Modern Dark UI**: A clean, premium interface inspired by Catppuccin color palettes.
- **Recursive Upload**: Automatically traverses directories to upload all files while maintaining folder structure.
- **Real-time Progress**: Visual progress bar and file counters to track your upload status.
- **Activity Log**: Detailed, color-coded logs for connection status, successful uploads, and errors.
- **Secure Credentials**: Dedicated fields for AWS Access Key, Secret Key, Bucket Name, and Region.
- **Asynchronous Operations**: Thread-safe implementation ensures the UI remains responsive during long-running uploads.
- **Cancellation Support**: Stop an ongoing upload at any time with a single click.

## 🚀 Getting Started

### Prerequisites

- **Python 3.x** installed on your system.
- An **AWS Account** with S3 access.
- **IAM Credentials** (Access Key ID and Secret Access Key).

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Bharanipbk/s3Uploader.git
   cd s3Uploader
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## 🛠️ Usage

1. **Launch the application**:
   ```bash
   python s3_uploader.py
   ```

2. **Configure your AWS settings**:
   - Enter your **Access Key ID** and **Secret Access Key**.
   - Provide the **Bucket Name** and **Region** (e.g., `us-east-1`).
   - (Optional) Set a **Key Prefix** to specify a destination folder within the bucket.

3. **Select your files**:
   - Click **📁 Browse** to select the local folder you wish to upload.

4. **Start the upload**:
   - Hit **🚀 Upload to S3** and watch the progress!

## 📦 Tech Stack

- **Language**: Python
- **GUI Framework**: Tkinter / Ttk
- **AWS SDK**: Boto3
- **Threading**: Standard `threading` and `queue` for non-blocking UI.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
Created with ❤️ by [Bharanipbk](https://github.com/Bharanipbk)
