# Contributing

This is a personal portfolio project built for internship applications, not
actively seeking external contributions right now. That said, if you spot a
bug or have a suggestion:

1. Open an issue describing what you found or what you'd like to see changed.
2. For code changes, fork the repo, make your change on a branch, and open a
   pull request against `main`.
3. Keep changes focused - one fix or feature per PR.
4. Before opening a PR, make sure the test suite passes:

   \\\
   cd backend
   python -m pytest ../tests/unit -v
   \\\

5. Run lint and typecheck on the frontend too:

   \\\
   cd frontend
   npm run lint
   npm run typecheck
   \\\

Thanks for taking a look at the project.
