# EasyTopics

**IMPORTANT:** Will be archived. This is (close to) the original version of EasyTopics, built as my solo project for the M.Sc. seminar “Practical Applications of Large Language Models” at LMU Munich. Frontend proudly presented by an early version of ChatGPT (GPT-3.5). It no longer runs as-is, as it depends on early versions of the OpenAI and LangChain libraries whose APIs have since changed. Development continues at [sfohr/easytopics](https://github.com/sfohr/easytopics/).

EasyTopics is a web app for question-guided topic modelling of open-ended text, e.g. survey responses. For a question or multiple questions you define, an LLM extracts the relevant part of each response. Only these extracted, and possibly pasted, answers are clustered, so the topics reflect your question rather than whatever dominates the raw text.

# Backend

Make sure to expose environment variables as stated in `backend/.env_template`.

# Built with:

- [Node.js](https://nodejs.org/en) 20.5.1
- [yarn](https://yarnpkg.com/) 1.22.19
- [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/) 3.3.3
- [Python](https://www.python.org/) 3.10.13

# Run development version

 Assert you have Python 3.10 installed, as well as Node.js and yarn.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Next we install the frontend dependencies:

```bash
cd frontend
yarn install
```

To run the backend exposed at localhost:5000, the clear flag is optional and removes the demo database. This takes a while at startup.

```bash
cd ../backend
bash start_backend.sh --clear
```

To run the frontend exposed at localhost:5173:

```bash
cd ../frontend
yarn dev
```

# License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Acknowledgments
Icon cat-curled by [svgrepo](https://www.svgrepo.com/svg/452950/cat-curled).
