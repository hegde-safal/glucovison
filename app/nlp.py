import spacy

class NLPEngine:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def parse_meals(self, text: str):
        """
        Extract food items and quantities.
        Returns list of (food_name, quantity).
        """
        if not text:
            return []

        doc = self.nlp(text)
        items = []
        
        def clean_name(tokens):
            text = " ".join([t.text for t in tokens if not t.is_punct and not t.like_num]).strip()
            # Remove stop words
            words = text.split()
            stop_words = {"a", "an", "the", "some", "of", "in", "with"}
            return " ".join([w for w in words if w.lower() not in stop_words])

        processed_tokens = set()
        
        # Logic matches Step 1 implementation
        for token in doc:
            if token.like_num:
                try:
                    qty = float(token.text)
                except ValueError:
                    continue
                
                head = token.head
                food_name = ""
                
                if head.text.lower() in ["cup", "cups", "slice", "slices", "piece", "pieces", "bowl", "bowls", "glass", "glasses", "plate", "plates"]:
                    of_child = next((c for c in head.children if c.text.lower() == "of"), None)
                    if of_child:
                        food_child = next((c for c in of_child.children if c.pos_ in ["NOUN", "PROPN"]), None)
                        if food_child:
                            food_tokens = [t for t in food_child.subtree]
                            # Include the unit in the name so API can use it (e.g. "slice of cheesecake")
                            base_name = clean_name(food_tokens)
                            food_name = f"{head.text} of {base_name}"
                            processed_tokens.update(food_tokens)
                else:
                    for chunk in doc.noun_chunks:
                        if head in chunk:
                            food_name = clean_name(chunk)
                            processed_tokens.update(chunk)
                            break
                    if not food_name:
                        food_name = head.text
                        processed_tokens.add(head)

                if food_name and len(food_name) > 1:
                    items.append((food_name, qty))
                    processed_tokens.add(token)

        for chunk in doc.noun_chunks:
            if any(t in processed_tokens for t in chunk):
                continue
            text = clean_name(chunk)
            if len(text) > 2:
                if not any(i[0] == text for i in items):
                    items.append((text, 1.0))
                    
        return items
