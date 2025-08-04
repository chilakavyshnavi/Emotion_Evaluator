#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
index.py - Vercel Serverless Function for Emotion Evaluator
==========================================================
Main entry point for Vercel deployment

File: index.py
Location: Root directory
"""

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import urllib.parse

# Import our sentiment analysis engine
from sentiment_engine import EmotionEvaluator


class SimpleSentimentAnalyzer:
    """Fallback sentiment analyzer using basic word lists"""

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
            "remarkable",
            "spectacular",
            "marvelous",
            "phenomenal",
            "splendid",
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
            "appalling",
            "atrocious",
            "deplorable",
            "detestable",
            "ghastly",
            "hideous",
            "loathsome",
            "miserable",
            "nasty",
            "revolting",
        }

    def analyze_text(self, text):
        """Simple sentiment analysis"""
        if not text or not text.strip():
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "message": "Empty text provided",
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
            "scores": {
                "confidence": round(confidence, 3),
                "confidence_percentage": round(confidence * 100, 1),
            },
            "metadata": {
                "text_length": len(text),
                "word_count": len(words),
                "analysis_timestamp": datetime.now().isoformat(),
                "api_version": "1.0",
                "method": "SimpleFallback",
            },
        }


# Initialize evaluator
try:
    evaluator = EmotionEvaluator()
except Exception:
    evaluator = None


class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set CORS headers for API responses"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send_json_response(self, data, status_code=200):
        """Send JSON response with proper headers"""
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()

        response = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(response.encode("utf-8"))

    def _send_error_response(self, message, status_code=400):
        """Send error response"""
        error_data = {
            "error": message,
            "timestamp": datetime.now().isoformat(),
            "status_code": status_code,
        }
        self._send_json_response(error_data, status_code)

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self._set_cors_headers()
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        path = self.path.split("?")[0]

        if path in ["/api/health", "/health"]:
            health_data = {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "evaluator_available": evaluator is not None,
                "platform": "Vercel Serverless",
            }
            self._send_json_response(health_data)
        else:
            self._send_error_response("Endpoint not found", 404)

    def do_POST(self):
        """Handle POST requests"""
        path = self.path.split("?")[0]

        if path not in ["/api/analyze", "/analyze"]:
            self._send_error_response("Endpoint not found", 404)
            return

        try:
            # Get content length
            content_length = int(self.headers.get("Content-Length", 0))

            if content_length == 0:
                self._send_error_response("No data provided")
                return

            # Read request body
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode("utf-8"))
            except json.JSONDecodeError:
                self._send_error_response("Invalid JSON format")
                return

            # Validate input
            if "text" not in data:
                self._send_error_response("Missing 'text' field")
                return

            text = data["text"]

            if not isinstance(text, str) or not text.strip():
                self._send_error_response("Text must be a non-empty string")
                return

            # Perform sentiment analysis
            if evaluator:
                # Use the full emotion evaluator if available
                result = evaluator.analyze_text(text)

                # Format for frontend
                if "error" not in result:
                    sentiment = result["sentiment"].lower()
                    confidence = result["confidence"]

                    emoji_map = {"positive": "😊", "negative": "😞", "neutral": "😐"}
                    message_map = {
                        "positive": "Positive sentiment detected!",
                        "negative": "Negative sentiment detected!",
                        "neutral": "Neutral sentiment detected",
                    }

                    formatted_result = {
                        "sentiment": sentiment,
                        "confidence": confidence,
                        "message": message_map.get(sentiment, "Sentiment analyzed"),
                        "emoji": emoji_map.get(sentiment, "🤔"),
                        "scores": {
                            "confidence": confidence,
                            "confidence_percentage": round(confidence * 100, 1),
                        },
                        "metadata": {
                            "text_length": len(text),
                            "word_count": len(text.split()),
                            "analysis_timestamp": datetime.now().isoformat(),
                            "api_version": "1.0",
                            "method": result.get("analysis_method", "EmotionEvaluator"),
                            "platform": "Vercel Serverless",
                        },
                    }
                else:
                    formatted_result = result
            else:
                # Use simple fallback analyzer
                simple_analyzer = SimpleSentimentAnalyzer()
                formatted_result = simple_analyzer.analyze_text(text)
                formatted_result["metadata"]["platform"] = "Vercel Serverless"

            self._send_json_response(formatted_result)

        except Exception as e:
            error_data = {
                "error": "Internal server error",
                "message": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            self._send_json_response(error_data, 500)


# This is the main entry point for Vercel
def main(request):
    """Main entry point for Vercel serverless function"""
    return handler(request, None)
