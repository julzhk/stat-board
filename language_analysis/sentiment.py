from textblob import TextBlob


def get_sentiment(txt):
    '''
    Return the sentiment for the most extreme sentence in the text supplied.
    :param text
    :return: -1 to 1
    '''
    txtblob = TextBlob(txt)
    sentences = txtblob.sentences
    sentiments = [sentence.sentiment.polarity for sentence in sentences]
    max_sentiment = max(sentiments)
    min_sentiment = min(sentiments)
    return max_sentiment  if max_sentiment > abs(min_sentiment) else min_sentiment