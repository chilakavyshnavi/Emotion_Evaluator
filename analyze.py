#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
api/analyze.py - Simple Sentiment Analysis API for Vercel
========================================================
"""

import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler


class SimpleSentimentAnalyzer:
    """Simple sentiment analyzer using word lists"""

    def __init__(self):
        self.positive_words = {
            "good",
            "great",
            "excellent",
            "amazing",
            "wonderful",
            "fantastic",
            "awesome",
            "love",
            "like",
            "enjoy",
            "happy",
            "pleased",
            "satisfied",
            "delighted",
            "perfect",
            "outstanding",
            "superb",
            "brilliant",
            "magnificent",
            "terrific",
            "best",
            "favorite",
            "recommend",
            "impressed",
            "beautiful",
            "nice",
            "positive",
            "fresh",
            "delicious",
            "tasty",
            "quality",
            "fast",
            "helpful",
            "incredible",
            "extraordinary",
        }

        self.negative_words = {
            "bad",
            "terrible",
            "awful",
            "horrible",
            "disgusting",
            "hate",
            "dislike",
            "disappointed",
            "unsatisfied",
            "unhappy",
            "angry",
            "frustrated",
            "annoyed",
            "worst",
            "poor",
            "cheap",
            "broken",
            "defective",
            "useless",
            "waste",
            "negative",
            "slow",
            "expensive",
            "rude",
            "dirty",
            "stale",
            "bland",
            "bitter",
            "sour",
            "wrong",
            "failed",
            "problem",
            "issue",
            "complaint",
            "disaster",
            "dreadful",
        }

    def analyze(self, text):
        """Analyze sentiment of text"""
        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "message": "Empty text",
                "emoji": "😐",
            }

        words = text.lower().split()
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)

        total_sentiment_words = positive_count + negative_count

        if total_sentiment_words == 0:
            return {
                "sentiment": "neutral",
                "confidence": 0.5,
                "message": "Neutral sentiment detected",
                "emoji": "😐",
            }

        sentiment_score = (positive_count - negative_count) / len(words)
        confidence = min(1.0, total_sentiment_words / max(1, len(words)) + 0.3)

        if sentiment_score > 0.05:
            sentiment = "positive"
            message = "Positive sentiment detected!"
            emoji = "😊"
        elif sentiment_score < -0.05:
            sentiment = "negative"
            message = "Negative sentiment detected!"
            emoji = "😞"
        else:
            sentiment = "neutral"
            message = "Neutral sentiment detected"
            emoji = "😐"

        return {
            "sentiment": sentiment,
            "confidence": round(confidence, 3),
            "message": message,
            "emoji": emoji,
            "metadata": {
                "text_length": len(text),
                "word_count": len(words),
                "positive_words": positive_count,
                "negative_words": negative_count,
                "timestamp": datetime.now().isoformat(),
            },
        }


# Initialize analyzer
analyzer = SimpleSentimentAnalyzer()


class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_json(self, data, status_code=200):
        """Send JSON response"""
        self._set_headers(status_code)
        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode("utf-8"))

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self._set_headers(200)

    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._send_json({"error": "No data provided"}, 400)
                return

            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_json({"error": "Invalid JSON"}, 400)
                return

            # Validate input
            if "text" not in data:
                self._send_json({"error": "Missing text field"}, 400)
                return

            text = data["text"]
            if not isinstance(text, str) or not text.strip():
                self._send_json({"error": "Text must be a non-empty string"}, 400)
                return

            # Analyze sentiment
            result = analyzer.analyze(text)
            self._send_json(result)

        except Exception as e:
            self._send_json({"error": "Internal server error", "message": str(e)}, 500)


# Vercel entry point
def main(request):
    """Main entry point for Vercel"""
    return handler(request, None)
