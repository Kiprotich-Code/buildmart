#!/usr/bin/env python3
"""
End-to-End Chat Feature Test Script

This script demonstrates the complete user flow for the chat feature:
1. User views products
2. User clicks chat button on a product
3. User is redirected to chat page with seller
4. Users can send and receive messages
5. Users can view chat history and manage conversations

Prerequisites:
- Django server running
- Test users and products in database
"""

import requests
import json
import time

# API Base URL
BASE_URL = "http://localhost:8000/api"

# Test user credentials
BUYER_CREDENTIALS = {
    "email": "buyer@test.com",
    "password": "testpass123"
}

SELLER_CREDENTIALS = {
    "email": "seller@test.com", 
    "password": "testpass123"
}

class ChatFeatureTest:
    def __init__(self):
        self.buyer_token = None
        self.seller_token = None
        self.product_id = None
        self.chat_id = None
        
    def login_user(self, credentials):
        """Login user and return auth token"""
        response = requests.post(f"{BASE_URL}/accounts/login/", json=credentials)
        if response.status_code == 200:
            return response.json().get('access')
        else:
            print(f"Login failed: {response.text}")
            return None
    
    def get_headers(self, token):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {token}"}
    
    def test_product_listing_with_chat_info(self):
        """Test 1: Get product listing with chat information"""
        print("\n=== TEST 1: Product Listing with Chat Info ===")
        
        response = requests.get(f"{BASE_URL}/products/products/")
        if response.status_code == 200:
            products = response.json()['results']
            if products:
                product = products[0]
                self.product_id = product['id']
                print(f"✓ Found product: {product['name']}")
                print(f"  - Price: ${product['price']}")
                print(f"  - Seller: {product['seller_name']}")
                print(f"  - Can chat: {product.get('can_chat', 'Not available')}")
                print(f"  - Existing chat: {product.get('existing_chat_id', 'None')}")
                return True
            else:
                print("✗ No products found")
                return False
        else:
            print(f"✗ Failed to get products: {response.text}")
            return False
    
    def test_authenticated_product_view(self):
        """Test 2: View product as authenticated user to see chat button"""
        print("\n=== TEST 2: Authenticated Product View ===")
        
        if not self.buyer_token:
            print("✗ No buyer token available")
            return False
            
        headers = self.get_headers(self.buyer_token)
        response = requests.get(f"{BASE_URL}/products/products/{self.product_id}/", headers=headers)
        
        if response.status_code == 200:
            product = response.json()
            print(f"✓ Product details retrieved: {product['name']}")
            print(f"  - Can chat: {product.get('can_chat', False)}")
            print(f"  - Existing chat: {product.get('existing_chat_id', 'None')}")
            print(f"  - Seller: {product['seller_name']} ({product['seller_email']})")
            return product.get('can_chat', False)
        else:
            print(f"✗ Failed to get product details: {response.text}")
            return False
    
    def test_start_chat_from_product(self):
        """Test 3: Start chat by clicking chat button on product"""
        print("\n=== TEST 3: Start Chat from Product ===")
        
        if not self.buyer_token:
            print("✗ No buyer token available")
            return False
            
        headers = self.get_headers(self.buyer_token)
        response = requests.post(f"{BASE_URL}/products/products/{self.product_id}/start_chat/", headers=headers)
        
        if response.status_code in [200, 201]:
            result = response.json()
            self.chat_id = result['chat']['id']
            print(f"✓ Chat {'created' if result['created'] else 'retrieved'}: {self.chat_id}")
            print(f"  - Buyer: {result['chat']['buyer']['email']}")
            print(f"  - Seller: {result['chat']['seller']['email']}")
            print(f"  - Product: {result['chat']['product']['name']}")
            return True
        else:
            print(f"✗ Failed to start chat: {response.text}")
            return False
    
    def test_send_message(self, token, sender_name, message_content):
        """Test 4: Send a message in the chat"""
        print(f"\n=== TEST 4: Send Message ({sender_name}) ===")
        
        if not token or not self.chat_id:
            print("✗ Missing token or chat ID")
            return False
            
        headers = self.get_headers(token)
        message_data = {
            "content": message_content,
            "message_type": "text"
        }
        
        response = requests.post(
            f"{BASE_URL}/chats/chats/{self.chat_id}/send_message/", 
            json=message_data, 
            headers=headers
        )
        
        if response.status_code == 201:
            message = response.json()
            print(f"✓ Message sent: {message['content']}")
            print(f"  - Sender: {message['sender']['email']}")
            print(f"  - Time: {message['created_at']}")
            return True
        else:
            print(f"✗ Failed to send message: {response.text}")
            return False
    
    def test_get_chat_messages(self, token, user_name):
        """Test 5: Get chat messages"""
        print(f"\n=== TEST 5: Get Chat Messages ({user_name}) ===")
        
        if not token or not self.chat_id:
            print("✗ Missing token or chat ID")
            return False
            
        headers = self.get_headers(token)
        response = requests.get(f"{BASE_URL}/chats/chats/{self.chat_id}/messages/", headers=headers)
        
        if response.status_code == 200:
            messages = response.json()
            print(f"✓ Retrieved {len(messages)} messages:")
            for msg in messages:
                print(f"  - {msg['sender']['email']}: {msg['content']} ({msg['created_at']})")
            return True
        else:
            print(f"✗ Failed to get messages: {response.text}")
            return False
    
    def test_get_user_chats(self, token, user_name):
        """Test 6: Get all chats for a user"""
        print(f"\n=== TEST 6: Get User Chats ({user_name}) ===")
        
        if not token:
            print("✗ No token available")
            return False
            
        headers = self.get_headers(token)
        response = requests.get(f"{BASE_URL}/chats/chats/", headers=headers)
        
        if response.status_code == 200:
            chats = response.json()['results']
            print(f"✓ Retrieved {len(chats)} chats:")
            for chat in chats:
                other_participant = chat['other_participant']
                last_msg = chat['last_message']
                print(f"  - Chat with {other_participant['email']}")
                print(f"    Product: {chat['product']['name']}")
                print(f"    Unread: {chat['unread_count']}")
                if last_msg:
                    print(f"    Last message: {last_msg['content'][:30]}...")
            return True
        else:
            print(f"✗ Failed to get chats: {response.text}")
            return False
    
    def test_mark_messages_as_read(self, token, user_name):
        """Test 7: Mark messages as read"""
        print(f"\n=== TEST 7: Mark Messages as Read ({user_name}) ===")
        
        if not token or not self.chat_id:
            print("✗ Missing token or chat ID")
            return False
            
        headers = self.get_headers(token)
        response = requests.patch(f"{BASE_URL}/chats/chats/{self.chat_id}/mark_as_read/", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ {result['message']}")
            return True
        else:
            print(f"✗ Failed to mark as read: {response.text}")
            return False
    
    def test_get_unread_count(self, token, user_name):
        """Test 8: Get unread message count"""
        print(f"\n=== TEST 8: Get Unread Count ({user_name}) ===")
        
        if not token:
            print("✗ No token available")
            return False
            
        headers = self.get_headers(token)
        response = requests.get(f"{BASE_URL}/chats/chats/unread_count/", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Unread messages: {result['unread_count']}")
            return True
        else:
            print(f"✗ Failed to get unread count: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run the complete end-to-end test suite"""
        print("🚀 Starting End-to-End Chat Feature Tests")
        print("=" * 50)
        
        # Login users
        print("\n=== User Authentication ===")
        self.buyer_token = self.login_user(BUYER_CREDENTIALS)
        self.seller_token = self.login_user(SELLER_CREDENTIALS)
        
        if not self.buyer_token:
            print("✗ Failed to login buyer")
            return
        if not self.seller_token:
            print("✗ Failed to login seller")
            return
            
        print("✓ Both users logged in successfully")
        
        # Run tests in sequence
        tests = [
            self.test_product_listing_with_chat_info,
            self.test_authenticated_product_view,
            self.test_start_chat_from_product,
            lambda: self.test_send_message(self.buyer_token, "Buyer", "Hi! I'm interested in this product. Is it still available?"),
            lambda: self.test_get_chat_messages(self.seller_token, "Seller"),
            lambda: self.test_send_message(self.seller_token, "Seller", "Hello! Yes, it's still available. Would you like more details?"),
            lambda: self.test_send_message(self.buyer_token, "Buyer", "Great! Can you tell me more about the condition?"),
            lambda: self.test_get_chat_messages(self.buyer_token, "Buyer"),
            lambda: self.test_get_user_chats(self.buyer_token, "Buyer"),
            lambda: self.test_get_user_chats(self.seller_token, "Seller"),
            lambda: self.test_mark_messages_as_read(self.seller_token, "Seller"),
            lambda: self.test_get_unread_count(self.buyer_token, "Buyer"),
            lambda: self.test_get_unread_count(self.seller_token, "Seller"),
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
                time.sleep(1)  # Small delay between tests
            except Exception as e:
                print(f"✗ Test failed with exception: {e}")
                failed += 1
        
        print("\n" + "=" * 50)
        print(f"🏁 Test Results: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 All tests passed! Chat feature is working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the output above.")


if __name__ == "__main__":
    # Instructions for running the test
    print("""
    📋 Chat Feature E2E Test Instructions:
    
    1. Make sure Django server is running: python manage.py runserver
    2. Create test users and products using Django admin or shell
    3. Update BUYER_CREDENTIALS and SELLER_CREDENTIALS if needed
    4. Run this script: python test_chat_feature.py
    
    This script will test the complete user flow:
    - Product listing with chat buttons
    - Starting chats from products
    - Sending and receiving messages
    - Chat management and notifications
    """)
    
    choice = input("\nPress Enter to start tests, or 'q' to quit: ")
    if choice.lower() != 'q':
        test = ChatFeatureTest()
        test.run_all_tests()
