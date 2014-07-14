import unittest
from sentiment import get_sentiment

class TestSentiment(unittest.TestCase):

    def test_positivecases(self):

        t = [
            'Designers, @barberosgerby have collaborated with @BMWGroup to create a memorable experience in the @V_and_A #LDF14 http://bit.ly/W2IDRu',
            "We've launched an exciting new learning project with @V_and_A  find out more about #ReelToReal http://bit.ly/1xR3bKc",
            "@V_and_A Spent half day at The V&A with my daughter Eva. She loved it, surrounded by beauty and history. Thanks! pic.twitter.com/sCAU9TRJNq"
            ]
        for txt in t:
            print txt
            self.assertTrue(get_sentiment(txt)>0.3)

    def text_ambivalentcases(self):
        t = [
            'more info on exciting exhibition about visual representation of protest that we are involved in @V_and_A here: http://www.vam.ac.uk/content/exhibitions/disobedient-objects/',
            'Really looking forward to Disobedient Objects - show of activist folk art - opening next week at @V_and_A pic.twitter.com/l2EjaqBVYt',
            '@V_and_A @sciencemuseum Congrats for making it into our 101 things to do in London for teenagers list #KidsLondon http://ow.ly/z82lQ',
        ]
        for txt in t:
            print txt
            self.assertTrue(-0.3< get_sentiment(txt) < 0.3)
    def text_badcases(self):
        t = [
            "We hate the boring new project with @V_and_A  find out more about #ReelToReal http://bit.ly/1xR3bKc",
        ]
        for txt in t:
            print txt
            self.assertTrue(get_sentiment(txt)<0.3)
