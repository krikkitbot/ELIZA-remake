This is an in-progress recreation of the original chatbot, ELIZA. ELIZA was created in the 1960s by Joseph Weizenbaum: https://cse.buffalo.edu/~rapaport/572/S02/weizenbaum.eliza.1966.pdf

This version of ELIZA has a response script largely faithful to the original, with text processing improved by the use of modern NLP tools.

She is a work-in-progress but entirely usable. She is currently unable to remember past input (even things that have just been said), which I would like to fix in the future. I may also integrate WordNet and FastText to give her a degree of semantic awareness.

Some considerations for use:
* ELIZA was designed to emulate a therapist, not a conversation partner. Keep the conversation about you--that's why she's here.
* Proper spelling and punctuation is recommended. She may get confused if certain words are misspelled or missing apostrophes. (Typing in all lowercase (OR ALL CAPS) is fine, though.)
* Be patient with her. She's a "dumb" chatbot--100% hardcoded (and by a single student under a time crunch)--and far from finished.
* Tell her "no" sparingly. She can and will ask you if something troubles you then accuse you of being negative if you answer "no." This is something I hope to alleviate when she can consider context (and semantics), but for now, consider rewording your "no" replies.

HOW TO RUN:
To talk to ELIZA, run eliza.py via the command line. Hitting Enter submits whatever you've typed. The conversation will continue until you tell her goodbye. You can also exit the program by typing "exit," hitting Ctrl-C, or closing the terminal.

You must have Python 3.10 installed, along with spaCy and its English module (en_core_web_sm) and pyinflect.
