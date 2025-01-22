# RUIT - CSV Integration for Ghunt 🌟

[![Gruvbox Dark](https://img.shields.io/badge/theme-Gruvbox%20Dark-%23A9B665?style=flat-square)](https://github.com/pindjouf/ruit)

RUIT is a sleek and intuitive CSV integration tool for [Ghunt](https://github.com/mxrch/GHunt), designed to make querying potential emails for people as smooth as possible. Just provide a CSV file with a `Name` column, and RUIT will handle the rest—automating email guesses and validating them via Ghunt.

---

## 🚀 Features

- Parse a CSV with a `Name` column and generate email guesses.
- Validate potential email addresses using Ghunt.
- Beautiful, color-themed console output with [Rich](https://github.com/Textualize/rich).
- Automatic handling of Ghunt authentication and session management.
- Output results to text files for discovered emails.

---

## 📦 Installation


1. Clone this repository:
   ```bash
   git clone https://github.com/pindjouf/ruit.git
   cd ruit
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Authenticate Ghunt:
   ```bash
   ghunt login
   ```

---

## 🛠 Usage

Run the script with the following command:
```bash
python ruit.py <input_file>
```

- `<input_file>`: Path to the CSV file containing a `Name` column with the names you want to process.

Example:
```csv
Name
John Doe
Jane Smith
```

The tool will:
1. Parse names and create email guesses like `john.doe@gmail.com`.
2. Query Ghunt for these potential emails.
3. Output results to `found_emails/`.

---

## ⚡ Example Output

```text
██████╗ ██╗   ██╗██╗████████╗
██╔══██╗██║   ██║██║╚══██╔══╝
██████╔╝██║   ██║██║   ██║   
██╔══██╗██║   ██║██║   ██║   
██║  ██║╚██████╔╝██║   ██║   
╚═╝  ╚═╝ ╚═════╝ ╚═╝   ╚═╝   

CSV integration for Ghunt

🔍 Processing: john.doe
✅ Found data for john.doe@gmail.com

🔍 Processing: jane.smith
⚠️  No data found for jane.smith@gmail.com
```

---

## 🤝 Contributing

Feel free to fork the repository and submit pull requests. Contributions are always welcome!

---

## 🛡 License

This *project* is licensed under the WTFPL License - see the [LICENSE](LICENSE) file for details.
