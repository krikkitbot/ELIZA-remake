import spacy
import en_core_web_sm
from pyinflect import getInflection
import re
import random

# initialize nlp
nlp = en_core_web_sm.load()

# dictionary mapping keywords to response types they trigger
keywords_initial = {}
keywords = {}
# dictionary containing responses, mapped to response type
responses = {}

def initialize_dictionaries():
    # reads keyword-response type pairs from a txt and puts them in the keyword dictionaries
    with open("initial_keywords.txt") as ikw_list:
        ikw_lines = ikw_list.readlines()
        for line in ikw_lines:
            line = line[:-1].split("\t") #line[:-1] removes trailing newline
            ikw, ikw_type = line[0], line[1]
            keywords_initial[ikw] = ikw_type
    
    with open("general_keywords.txt") as kw_list:
        kw_lines = kw_list.readlines()
        for line in kw_lines:
            line = line[:-1].split("\t")
            kw, kw_type = line[0], line[1]
            keywords[kw] = kw_type
    
    # same as above, but with response types responses
    # some response types have more than one possible response, so responses are stored in a list
    with open("responses.txt") as r_list:
        r_lines = r_list.readlines()
        for line in r_lines:
            line = line[:-1].split("\t")
            r_type, r_set = line[0], line[1:]
            responses[r_type] = r_set
    
    
def run_command(str):
    if "!exit" in str:
        exit()
        

def fill_blank(kw, str, user_input):
    # substring to insert into response
    substr = ""
    # checks the complement of certain verbs which permit propositional complements
    # identifies NPs and VPs in the complement and chooses one at random to respond to
    if "$comp" in str:
        # first, extract the complement of the key verb
        pattern = ".*"+kw
        comp = re.sub(pattern,"",user_input.text)
        comp = re.sub("[\.\?\!;]+.*","",comp)
        # then, convert it to a spacy doc
        comp = nlp(comp)
        # identify all nouns and verbs (including the copula)
        valid_heads = []
        for token in comp:
            if token.pos_ == "NOUN" or token.pos_ == "PROPN" or token.pos_ == "VERB" or token.lemma_ == "be":
                valid_heads.append(token)
        # verify that at least 1 valid token has been found
        if len(valid_heads) > 0:
            # choose one at random and extract its subtree
            n = random.randint(0,len(valid_heads)-1)
            subtree = valid_heads[n].subtree
            # convert the subtree to a string, making the necessary grammatical transformations
            for token in subtree:
                if token.pos_ == "PRON" and token.dep_ == "nsubj":
                    substr += make_accusative(token.text)
                elif (token.pos_ == "VERB" or token.lemma_ == "be"):
                    substr += getInflection(token.lemma_,"VBG")[0]
                else:
                    substr += token.text
                substr += " "
        # if nothing can be extracted, use "that"
        else:
            substr = "that "
        # convert indefinite articles to definite
        re.sub(" an? "," the ",substr)
        # remove trailing and leading spaces and insert substring in place of $comp
        # complementizers can wind up persisting and resulting in odd grammar, so this removes them too
        substr = re.sub("(^ +(that )?| +$)","",substr)
        return re.sub("\$comp",substr,str)
    # lifts quotes verbatim from input
    elif "$quot" in str:
        # same as above
        pattern = ".*"+kw
        substr = re.sub(pattern,"",user_input.text)
        substr = re.sub("[\.\?\!;]+.*","",substr)
        # then return it without leading/trailing spaces
        substr = re.sub("(^ +| +$)","",substr)
        return re.sub("\$quot",substr,str)
    # same as the above, but functions in the absence of a keyword
    # it parrots back the entire input sentence
    elif "$parrot" in str:
        substr = re.sub("(^ +|[\.\?\!;].*| +$)","",user_input.text)
        return re.sub("\$parrot",substr,str)
    # processes the predicate of the copula
    elif "$pred" in str:
        # remove subject pronoun, if present
        if len(kw.split()) > 1:
            kw = kw.split()[1]
        # extract the predicate (including the copula) and convert it to a doc
        pattern = ".*"+kw
        pred = re.sub(pattern,kw,user_input.text)
        pred = re.sub("[\.\?\!;]+.*","",pred)
        pred = nlp(pred)
        # find the root
        for token in pred:
            if token.dep_ == "ROOT":
                if token.lemma_ == "be":
                    # if the root is the copula, identify its child, if any
                    if token.is_ancestor:
                        child = next(token.children)
                        # randomly extract either full constituent or only the relevant word
                        if random.randint(0,1) == 1:
                            for token in child.subtree:
                                substr += token.text + " "
                        else:
                            # don't return a noun without its determiner
                            if child.pos_ == "NOUN" and child.is_ancestor:
                                if next(child.children).pos_ == "DET":
                                    substr = next(child.children).text + " "
                                    # correct the article if removing an adjective messed it up
                                    if substr == "a " and re.search("^[aeiou]",child.text):
                                        substr = "an "
                                    elif substr == "an " and re.search("^[^aeiou]",child.text):
                                        substr = "a "
                            substr += child.text
                        # exit the for loop
                        break
                    # if no children exist, return an empty string
                    else:
                        return ""
                # if "be" serves as an auxiliary, the main verb is the root
                # in this case, just return the whole thing, minus the auxiliary
                else:
                    for token in pred[1:]:
                        substr += token.text + " "
                    break
        # finally, return the response
        substr = re.sub("(^ +| +$)","",substr)
        return re.sub("\$pred",substr,str)
    # extracts the subject
    elif "$subj" in str:
        # get rid of everything after the triggering verb
        pattern = kw+".*"
        initial = re.sub(pattern,kw,user_input.text)
        # create the spacy doc
        initial = nlp(initial)
        # use dependency relations to identify the subject
        # this is in case it exists within an embedded clause
        if len(initial) > 0:
            subj = initial[-1].subtree
            # convert the subject tree to a string
            for token in subj:
                substr += token.text + " "
        # if no subject is found, use a generic one
        else:
            substr = "they"
        # remove the verb and leading/trailing spaces before returning
        pattern = "(^ +| (" + kw + ")? *$)"
        substr = re.sub(pattern,"",substr)
        return re.sub("\$subj",substr,str)
    # extracts the head noun from a possessive NP
    elif "$poss" in str:
        # remove anything before the possessive NP
        pattern = ".*"+kw
        trimmed = re.sub(pattern,kw,user_input.text)
        # create the doc
        trimmed = nlp(trimmed)
        # identify the head noun
        substr = next(trimmed[0].ancestors).text
        # return it
        return re.sub("\$poss",substr,str)
    # gets the object of a verb
    elif "$obj" in str:
        # remove the triggering verb and everything before it
        pattern = ".*"+kw
        pred = re.sub(pattern,"",user_input.text)
        # convert to a spacy doc
        pred = nlp(pred)
        # take the first NP in the remaining text
        # this isn't foolproof, but $obj is only called in a couple specific contexts where this is unlikely to go wrong, so it's more practical than using the dependency parser
        # the loop is to avoid triggering an iteration error if there are no NPs
        for np in pred.noun_chunks:
            for token in np:
                substr += token.text + " "
            # only one NP is needed, so break the loop
            break
        if len(substr) == 0:
            # if no NPs are found, give a default response
            # this response is tailored to the specific contexts $obj is called in
            substr = "this person"
        # as always, remove extraneous spaces and return
        substr = re.sub("(^ +| +$)","",substr)
        return re.sub("\$obj",substr,str)
    

def swap_persons(input_doc):
    # create a new string
    new_text = ""
    # add each token to new string sequentially, swapping persons if necessary
    for token in input_doc:
        match token.text:
            case "i":
                # if preceded by "am" or "was", first change verb
                if new_text.endswith("am "):
                    new_text = re.sub("am $","are ",new_text)
                if new_text.endswith("was "):
                    new_text = re.sub("was $","were ",new_text)
                # then invert pronoun
                new_text += "you "
            case "me" | "we" | "us":
                new_text += "you "
            case "my" | "our":
                new_text += "your "
            case "mine" | "ours":
                new_text += "yours "
            case "myself":
                new_text += "yourself "
            case "ourselves":
                new_text += "yourselves "
            case "you":
                # if preceded by "are" or "were", first change verb
                if new_text.endswith("are "):
                    new_text = re.sub("are $","am ",new_text)
                if new_text.endswith("were "):
                    new_text = re.sub("were $","was ",new_text)
                # then invert pronoun according to case
                if token.dep_ == "nsubj":
                    new_text += "I "
                else:
                    new_text += "me "
            case "your":
                new_text += "my "
            case "yours":
                new_text += "mine "
            case "yourself":
                new_text += "myself "
            case "am" | "'m":
                new_text += "are "
            case "was":
                # convert to "were" iff token follows "you" (swapped from "i")
                if new_text.endswith("you "):
                    new_text  += "were "
            case "are" | "'re":
                # convert to "am" iff token follows "i" (swapped from "you")
                if new_text.endswith("i "):
                    new_text += "am "
                else:
                    new_text += "are "
            case "were":
                # same as above, but for past tense
                if new_text.endswith("i "):
                    new_text += "was "
                else:
                    new_text += "were "
            case "n't":
                # for ease of processing; this was a convenient place to put it
                new_text += "not "
            case other:
                # remove trailing space if appending punctuation
                if token.is_punct:
                    new_text = new_text[:-1]
                new_text += token.text + " "
    # return transformed text as spacy doc
    return nlp(new_text)


def make_accusative(pronoun):
    match pronoun:
        case "i":
            return "me"
        case "we":
            return "us"
        case "he":
            return "him"
        case "she":
            return "her"
        case "they":
            return "them"
    return pronoun


# method to generate a response to input according to response type
# some responses trigger additional transformations
def respond(kw, r_type, user_input):
    # get possible responses
    possible_responses = responses[r_type]
    # select one response at random
    r = possible_responses[random.randint(0,len(possible_responses)-1)]
    # check for special tokens in response
    if "!" in r:
        run_command(r)
    while "$" in r:
        r = fill_blank(kw, r, user_input)
    return r
            

def process(user_input):
    output = ""
    # first, swap all instances of first- and second-person pronouns
    user_input = swap_persons(user_input)
    # next, split response into sentences
    input_tokenized = re.split("(?<=[.!?;]) +",user_input.text)
    for sentence in input_tokenized:
        # convert to spacy doc
        sentence = nlp(sentence)
        # check if sentence starts with a recognized phrase-initial keyword
        # the second half of the if statement ensures it isn't mistaking a piece of a word for a keyword (e.g., "yesterday" for "yes")
        for kw in keywords_initial.keys():
            if sentence.text.startswith(kw) and sentence[0].text in kw:
                # passes response type and input to respond() method
                output = respond(kw,keywords_initial[kw],sentence) + " "
                # then check for other keywords
                for kw in keywords.keys():
                    if kw in sentence.text:
                        output += respond(kw,keywords[kw],sentence) + " "
    # if no appropriate response can be generated, use a default one
    if len(output) == 0:
        if "?" in user_input.text:
            output = respond(None,"QUESTION",user_input) + " "
        else:
            output = respond(None,"NONE",user_input)
    # finally, return output
    return output

def main():
    # initialize keyword and stock response dictionaries
    initialize_dictionaries()
    
    # initial prompt
    print("ELIZA:\tHow do you do? Please tell me your problem.")
    
    # loop that runs the chat indefinitely
    while(True):
        # get user input and convert it to a spacy doc
        user_input = nlp(input("YOU:\t").lower())
        # process the input and generate output
        output = process(user_input)
        # print the output
        print("ELIZA:\t" + output)


main()