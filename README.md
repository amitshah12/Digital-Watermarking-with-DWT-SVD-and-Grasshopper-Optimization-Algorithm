# Digital Watermarking using DWT–SVD with Grasshopper Optimization (GOA)

A robust and imperceptible **digital image watermarking system** that combines **Discrete Wavelet Transform (DWT)**, **Singular Value Decomposition (SVD)**, and the **Grasshopper Optimization Algorithm (GOA)** to automatically optimize embedding strength and improve watermark quality.

---

## Overview

Digital media is highly vulnerable to unauthorized copying and tampering. Traditional watermarking methods often use fixed embedding parameters, which can compromise either **image quality** or **robustness**.

This project proposes a **hybrid DWT–SVD watermarking framework** in which the embedding strength (α) is **adaptively optimized using GOA** to achieve:

* High imperceptibility
* Strong robustness against common image processing attacks
* Reliable watermark extraction

A **Flask-based web application** allows users to embed, extract, and evaluate digital watermarks through an interactive interface.

---

## Key Features

* Hybrid **DWT–SVD watermarking**
* **GOA-based adaptive optimization** of embedding strength
* Embedding in the **HL sub-band** for a quality–robustness balance
* Performance evaluation using:

  * PSNR
  * SSIM
  * MSE
  * NCC
* Robustness evaluation against:

  * JPEG compression
  * Gaussian noise
  * Salt & Pepper noise
  * Blurring
* Interactive **Flask web interface**

---

## Methodology

The watermarking process follows these main steps:

1. Apply **DWT** to decompose the cover image.
2. Perform **SVD** on the selected frequency sub-band (HL).
3. Apply **SVD** to the watermark image.
4. Use **GOA** to determine the optimal embedding strength (α).
5. Modify the singular values and reconstruct the watermarked image.
6. Extract the watermark using the corresponding inverse operations.

---

## System Architecture

<p align="center">
  <img src="Project_Screenshot/block_diagram.png" width="400">
</p>

---

## Web Application Interface

<p align="center">
  <img src="Project_Screenshot/UI.jpeg" width="320">
  <img src="Project_Screenshot/UI-in_out.jpeg" width="320">
</p>

The web application allows users to:

* Upload a cover image and watermark image
* Automatically optimize α using GOA
* Generate and download the watermarked image
* Extract the embedded watermark
* Evaluate watermarking performance using quality metrics

---

## Results & Performance

<p align="center">
  <img src="Project_Screenshot/Result_view.png" width="320">
  <img src="Project_Screenshot/metric.png" width="320">
</p>

### Quantitative Results

The following results were obtained from a representative experiment using the selected cover image, watermark, and optimized embedding strength.

| Metric    |        Value |
| --------- | -----------: |
| PSNR      | **51.13 dB** |
| SSIM      |   **0.9968** |
| NCC       |     **0.99** |
| Optimal α |     **0.01** |

### Interpretation

* **PSNR > 50 dB** indicates high imperceptibility for the tested image.
* **SSIM close to 1** indicates high structural similarity between the original and watermarked images.
* **NCC close to 1** indicates accurate watermark recovery.

---

## Tech Stack

* **Language:** Python
* **Framework:** Flask
* **Libraries:**

  * OpenCV
  * NumPy
  * PyWavelets
  * SciPy
  * scikit-image

---

## Tested Environment

This project has been tested with the following environment:

| Component    | Version          |
| ------------ | ---------------- |
| Python       | 3.12.10 (64-bit) |
| Flask        | 2.3.3            |
| NumPy        | 1.26.4           |
| OpenCV       | 4.8.1.78         |
| PyWavelets   | 1.9.0            |
| scikit-image | 0.22.0           |
| Werkzeug     | 2.3.7            |

> **Recommended Python version:** Python 3.12 (64-bit).
>
> Python 3.14 may not be compatible with some of the pinned scientific computing dependencies used in this project.

---

## Project Structure

```text
Digital-Watermarking-with-DWT-SVD-and-Grasshopper-Optimization-Algorithm/
│
├── backend/
│   ├── algorithms/
│   │   ├── dwt_transform.py
│   │   ├── svd_transform.py
│   │   ├── goa_optimizer.py
│   │   ├── watermark_embedding.py
│   │   └── watermark_extraction.py
│   │
│   ├── utils/
│   │   └── metrics.py
│   │
│   ├── routes/
│   │   └── watermark_routes.py
│   │
│   └── app.py
│
├── templates/
├── static/
├── data/
│   └── sample_images/
│
├── Project_Screenshot/
│   ├── block_diagram.png
│   ├── UI.jpeg
│   ├── UI-in_out.jpeg
│   ├── Result_view.png
│   └── metric.png
│
├── requirements.txt
├── setup.py
├── README.md
└── .gitignore
```

---

# How to Run

## 1. Clone the Repository

```bash
git clone https://github.com/amitshah12/Digital-Watermarking-with-DWT-SVD-and-Grasshopper-Optimization-Algorithm.git
cd Digital-Watermarking-with-DWT-SVD-and-Grasshopper-Optimization-Algorithm
```

---

## 2. Create and Activate a Virtual Environment

Make sure you have **Python 3.12 (64-bit)** installed.

### Windows

Create the virtual environment using Python 3.12:

```bash
py -3.12 -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

Verify the Python version:

```bash
python --version
```

Expected output:

```text
Python 3.12.x
```

You can also verify that you are using a 64-bit Python installation:

```bash
python -c "import platform; print(platform.architecture())"
```

Expected output:

```text
('64bit', 'WindowsPE')
```

### Linux/macOS

Create and activate the virtual environment:

```bash
python3.12 -m venv venv
source venv/bin/activate
```

---

## 3. Upgrade pip

Before installing the project dependencies, upgrade pip and the required packaging tools:

```bash
python -m pip install --upgrade pip setuptools wheel
```

---

## 4. Install Dependencies

Install all required dependencies:

```bash
pip install -r requirements.txt
```

After successful installation, you can verify the installed packages:

```bash
pip list
```

---

## 5. Run the Flask Application

Inside the **backend/** folder, the entry point is `app.py`.

```bash
cd backend
python app.py
```

This will start the Flask development server, typically at:

```text
http://127.0.0.1:5000/
```

---

## 6. Access the Web Interface

Open your browser and navigate to:

```text
http://127.0.0.1:5000/
```

You can then:

* Upload a cover image
* Upload a watermark image
* Embed the watermark
* Automatically optimize the embedding strength using GOA
* Download the watermarked image
* Extract the watermark
* Evaluate the watermarking performance

---

## 7. (Optional) Run Algorithm Scripts Directly

If you want to experiment with the watermarking pipeline without running the web interface:

```bash
python algorithms/watermark_embedding.py
python algorithms/watermark_extraction.py
```

---

# Troubleshooting

## NumPy or PyWavelets Installation Fails

If pip attempts to build NumPy or PyWavelets from source and you encounter compiler-related errors, first check your Python version:

```bash
python --version
```

Also check your Python architecture:

```bash
python -c "import platform; print(platform.architecture())"
```

This project has been tested with:

```text
Python 3.12.x
('64bit', 'WindowsPE')
```

If you previously created the virtual environment using another Python version, delete and recreate it.

### Windows

First deactivate the existing environment:

```bash
deactivate
```

Delete the existing virtual environment:

```bash
rmdir /s /q venv
```

Create a new environment using Python 3.12:

```bash
py -3.12 -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

Then reinstall the dependencies:

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

---

# Key Contributions

* Designed a **hybrid DWT–SVD–GOA watermarking system**
* Implemented **metaheuristic optimization** for adaptive watermark embedding
* Developed a complete **Flask-based web application**
* Achieved high image quality in representative experiments, including **PSNR of 51.13 dB** and **SSIM of 0.9968**
* Evaluated robustness against multiple common image distortions

---

# Limitations

* Higher computation time due to GOA optimization
* Semi-blind extraction requires knowledge of the optimized embedding strength (α)
* Limited resistance to geometric attacks such as rotation and scaling

---

# Future Work

* Deep learning–based watermarking
* Video and audio watermarking
* Improved resistance to geometric attacks
* GPU acceleration for faster optimization
* Blockchain-based ownership verification

---

# Author

**Amit Shah**
B.Tech Computer Science (Final Year)

GitHub: https://github.com/amitshah12