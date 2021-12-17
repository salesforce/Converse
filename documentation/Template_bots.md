# Template Bots

We provide 6 template bots: online shopping, health appointment, book movie tickets, online banking, customize a T-shirt, 
and book a flight.

These template bots are used for different scenarios. You can refer to them when you build your own Converse chatbot.

## Online shopping
```yaml
Task:
  verify_user:
    description: pull up your account
    samples:
    entities:
      email_address:
        function: http://localhost:9002/entity_service/single_step_verify
        confirm: yes
        prompt:
        response:
      zip_code:
        function: http://localhost:9002/entity_service/single_step_verify
        confirm: no
        prompt:
        response:
    entity_groups:
      email_address_group:
        - email_address
      zip_code_group:
        - zip_code
    success:
      OR:
        - VERIFY:
            - email_address_group
        - VERIFY:
            - zip_code_group
    finish_response:
      success:
        - I have verified your identity.
      failure:
        - Sorry, I can't verify your identity.
    repeat: false
    max_turns: 8

  check_order:
    description: check your order status
    samples:
      - I have not received the ordered item yet
      - The ordered item has not yet delivered
      - is my ordered item on the way?
      - i want to check my order
      - my order status
      - check order status
      - order status
    entities:
      oid:
        function: http://localhost:9002/entity_service/get_order_status
        confirm:
        prompt:
          - Please provide your order id for your order status.
        response:
          - One moment please. Your order status is <info>.
    entity_groups:
      order_id_group:
        - oid
    success:
      AND:
        - TASK:
            - verify_user
        - QUERY:
            - order_id_group
    finish_response:
      success:
        - That is all the information that I have on your order status.
      failure:
        - Sorry, I can't help you check your order status.
    repeat: true
    repeat_response:
      - Would you like to check the status of another order?
    max_turns: 10

  update_order:
    description: add more to your order
    samples:
      - Please add more items to my order
      - Please add another item to my order
      - Can you add more to my order
    entities:
      oid:
        function: collect_info
        confirm: no
        prompt:
          - Could you please tell me the order id of the item that you want to order more of?
        response:
          - Sure.
      quantity:
        function: http://localhost:9002/entity_service/add_more_to_order
        confirm: yes
        prompt:
          - How many do you want to add?
        response:
          - Got it. Now you have ordered <info> pieces.
        retrieve: false
    entity_groups:
      order_quantity_group:
        - oid
        - quantity
    success:
      AND:
        - TASK:
            - verify_user
        - UPDATE:
            - order_quantity_group
    finish_response:
      success:
        - Your order has been updated.
      failure:
        - Sorry, I can't help you add more items to your order.
    repeat: true
    repeat_response:
      - Would you like to add more items to your order?
    max_turns: 10
```
We defined 3 tasks for the online shopping assistant bot. `check_order` and `update_order` are the two main tasks, which allows you to check order status and add more items to an existing order.
`verify_user` is a sub-task, which is shared by `check_order` and `update_order`. When a user wants to do `check_order` or `update_order`, the sub-task `verify_user` will be triggered first to verify the user's identity.
Note that we didn't provide any sample utterances for the `verify_user` task. `verify_user` can only be triggered when the user wants to do `check_order` or `update_order`.

This bot also used a database, which we call `simple_db`. You may find this example useful when your own bot needs a database.
We wrapped up `simple_db` in RESTful APIs. You can see that, in the task configuration, the entity functions are URLs of these APIs.

Note that, if you run the entity service backend (`Converse/entity_backend/entity_service_backend.py`) manually, you may need to change the start of the URLs from `http://localhost:9002/entity_service/` to `http://localhost:8001/` in the task configuration file.

An example conversation between this bot and the user is below:
```
BOT: Hi there, I am the digital assistant for Northern Trail information Center. What can I do for you?
ME: I want to check order status.
BOT: Oh sure, I'd be happy to help you check your order status. First, I need to pull up your account. Can I get your email address?
ME: 3@g.com
BOT: Okay, so 3@g.com?
ME: yes
BOT: I am sorry, but I could not recognize your email_address. What is your zip code?
ME: 94301
BOT: Okay. I have verified your identity. Please provide your order id for your order status.
ME: my order id is 1
BOT: One moment please. Your order status is placed but not yet shipped. That is all the information that I have on your order status. Would you like to check the status of another order?
ME: no
BOT: Is there anything else I can help you with today?
ME: I want to add more to my order
BOT: Oh sure, I’d be happy to help you add more to your order. Your oid is 1. Is that correct?
ME: yes
BOT: Sure. How many do you want to add?
ME: 15
BOT: Okay, so 15?
ME: yes
BOT: Got it. Now you have ordered 25 pieces. Your order has been updated. Would you like to add more items to your order?
ME: no
BOT: Is there anything else I can help you with today?
ME: no. thank you!
BOT: Sounds good. I'm glad I could help. Thanks for calling, and have a good one.
```

## Health appointment
```yaml
Task:
  get_health_insurance_info:
    description: get health insurance info
    entities:
      ssn:
        function: verify_ssn
        confirm: no
        prompt:
          - May I have the last four digits of your social security number?
        response:
      birthday:
        function: verify_ssn
        confirm: no
        prompt:
          - And your birthday?
        response:
    entity_groups:
      ssn_group:
        - ssn
      birthday_group:
        - birthday
    success:
      AND:
        - VERIFY:
          - ssn_group
        - VERIFY:
          - birthday_group
    finish_response:
      success:
        - I have found your health insurance record.
      failure:
        - Sorry, I am not able to find your health insurance record.
    repeat: false
    max_turns: 10

  health_appointment:
    description: make an appointment at Nurse Nancy
    samples:
      - I want to see a doctor
      - I don't feel so good
      - I would like to make an appointment
      - I want to make an appointment
      - I got a fever
      - make an appointment at Nurse Nancy
    entities:
      appt_date:
        function: collect_info
        confirm: no
        prompt:
          - What date do you prefer for the appointment?
        response:
      appt_time:
        function: collect_info
        confirm: no
        prompt:
          - At what time?
        response:
      department:
        function: collect_info
        confirm: no
        prompt:
          - Which department do you want to make the appointment with?
        response:
      doctor_name:
        function: collect_info
        confirm:
        prompt:
        response:
      covid_protocol:
        function: covid_protocol
        confirm: no
        prompt:
        response:
          - <info>
      have_health_insurance:
        function: check_condition
        confirm: no
        prompt:
          - Do you have health insurance?
        response:
          - <info>
      name:
        function: collect_info
        confirm: no
        prompt:
          - Since you don't have health insurance, let me create a profile for you. What's your name?
        response:
      birthday:
        function: collect_info
        confirm: no
        prompt:
          - What is your birthday?
        response:
          - I have created a profile for you.
    entity_groups:
      date_time_group:
        - appt_date
        - appt_time
      department_doctor_group:
        - department
        - doctor_name
      covid_protocol_group:
        - covid_protocol
      have_health_insurance_group:
        - have_health_insurance
      name_birthday_group:
        - name
        - birthday
    success:
      AND:
        - INSERT:
          - date_time_group
        - INSERT:
          - department_doctor_group
        - OR:
          - AND:
            - API:
              - have_health_insurance_group
            - TASK:
              - get_health_insurance_info
          - INSERT:
            - name_birthday_group
        - INFORM:
          - covid_protocol_group
    finish_response:
      success:
        - I have booked an appointment for you.
      failure:
        - Sorry, I can't help you book an appointment.
    task_finish_function: create_appointment
    repeat: true
    repeat_response:
      - Would you like to make another appointment?
    max_turns: 10
```
We defined 2 tasks for the health appointment bot. `health_appointment` is the main task, which has a sub-task `get_health_insurance_info`. 
This bot allows you to make an appointment at Nurse Nancy. 

We use `collect_info` for several entities in `health_appointment`. This function collects the information provided by the 
user, and it doesn't process the information immediately. In `health_appointment`, there's a task finish function `create_appointment` 
to process all the entities after this task finishes.

In this bot, we used an and-or structure to mimic an if-else logic, see below.
```yaml
- OR:
  - AND:
    - API:
      - have_health_insurance_group
    - TASK:
      - get_health_insurance_info
  - INSERT:
    - name_birthday_group
```

The `API: - have_health_insurance_group` is a yes-or-no condition check. If this condition is `True`, then `TASK: - get_health_insurance_info` 
can be triggered. The agent will try to verify the user's insurance information. If `API: - have_health_insurance_group` returns `False`, then `TASK: - get_health_insurance_info` will not be triggered. In this case, `- INSERT: - name_birthday_group`
Will be triggered. The agent will try to create a new profile for the user. 

It's just like 
```python
if have_health_insurance:
   TASK: - get_health_insurance_info
else:
   INSERT: - name_birthday_group
```
However, this doesn't perfectly mimic the if-else logic. If `TASK: - get_health_insurance_info` is triggered, but the 
user's health insurance information cannot be verified, `- INSERT: - name_birthday_group` will still be triggered, even 
if the condition check returns `True`.

Since the and-or relation we defined contain order, the example below can also represent if-else logic actually:
```yaml
- OR:
  - TASK:
    - get_health_insurance_info
  - INSERT:
    - name_birthday_group
```
In this example, if `- TASK: - get_health_insurance_info` cannot get correct results,  `- INSERT: - name_birthday_group` 
will be executed.

An example conversation between the health appointment bot and the user is below:
```
BOT: Hi there, I am Nurse Nancy. What can I do for you?
ME: I want to see a doctor.
BOT: Oh sure, I’d be happy to help you make an appointment at Nurse Nancy. What date do you prefer for the appointment?
ME: tomorrow
BOT: Got it. At what time?
ME: at 11am
BOT: Got it. Which department do you want to make the appointment with?
Your choices are listed here:
- ICU
- Elderly services
- Diagnostic Imaging
- General Surgery
- Neurology
- Microbiology
- Nutrition and Dietetics
ME: general surgery
BOT: Okay. May I have your preferred doctor name?
ME: Harry
BOT: Okay. Do you have health insurance?
ME: yes
BOT: OK. May I have the last four digits of your social security number?
ME: 1234
BOT: Got it. Your birthday is December 9, 2021. Is that correct?
ME: no. my birthday is Aug 1, 1980
Bot: Got it. I have found your health insurance record. If you have COVID-19 symptoms, immediately self-isolate and contact your local public health authority or healthcare provider. Wear a mask, stay at least 6 feet from others, wash your hands, avoid crowds, and take other steps to prevent the spread of COVID-19. Would you like to make another appointment?
ME: no
BOT: Is there anything else I can help you with today?
ME: no. thank you!
BOT: Sounds good. I'm glad I could help. Thanks for calling, and have a good one.
```

## Book movie tickets
```yaml
Task:
  book_movie_tickets:
    description: book movie tickets at Old Movie Theater
    samples:
    - I want to see a movie
    - I would like to see a movie
    - I want to buy movie tickets
    - Can I buy tickets for a movie
    entities:
      movie_name:
        function: collect_info
        confirm: false
        prompt:
          - Which movie do you want to see?
        response:
          - Great choice!
      movie_date:
        function: collect_info
        confirm: false
        prompt:
          - What date do you prefer?
        response:
          - Got it.
      movie_time:
        function: collect_info
        confirm: false
        prompt:
          - And what time?
        response:
          - Got it.
      ticket_quantity:
        function: collect_info
        confirm: false
        prompt:
          - How many tickets do you want to buy?
        response:
          - All set.
    entity_groups:
      ticket_info_group:
        - movie_name
        - movie_date
        - movie_time
        - ticket_quantity
    success:
      AND:
        - API:
            - ticket_info_group
    finish_response:
      success:
        - I booked your tickets. I look forward to seeing you at Old Movie Theater.
      failure:
        - Sorry, I am not able to book your tickets.
    repeat: false
    repeat_response: []
    task_finish_function: finish_booking_movie_tickets
    max_turns: 10
    
  movies_in_theater:
    description: share with you the movies being shown in Old Movie Theater right now
    samples:
      - what movies are being shown today?
      - I want to know what movies are being shown
      - tell me the movies being shown in the theater
    entities:
      inform_movie_names:
        function: movies_being_shown
        confirm: false
        prompt: []
        response:
          - <info>
    entity_groups:
      movie_name_group:
        - inform_movie_names
    success:
      AND:
        - INFORM:
            - movie_name_group
    finish_response:
      success: []
      failure: []
    repeat: false
    repeat_response: []
    task_finish_function: null
    max_turns: 10
FAQ:
  parking:
    samples:
    - Do you have any instructions for parking?
    - Where do I park my car?
    - Where is the parking lot?
    - car parking
    - parking
    answers:
    - Convenient, free guest parking is located next to the theater. The entrance to the 7-story
      parking garage is off California Street, past the front of the theater.
    question_match_options:
    - fuzzy_matching
    - nli
```
We have 2 tasks in this movie tickets bot. Users can use the `book_movie_tickets` task to book movie tickets, or use `movies_in_theater` 
task to check the movies currently being shown.

Like in the health appointment bot, we use `collect_info` for several entities in the `book_movie_tickets` task. There's a task
finish function `finish_booking_movie_tickets` to process all the entities after this task finishes. `movies_in_theater`
task is simple. When this task is triggered, it will return the movie list to the user.

We provide `parking` as an example of `FAQ` in this bot. When users ask for parking instructions, the bot will respond the answer 
to the users.

An example conversation between this bot and the user is below:
```
BOT: Hi there, I am the digital assistant for Old Movie Theater. What can I do for you?
ME: Hi, what movies are being shown today?
BOT: Here are the movies in theater now:
- The Shawshank Redemption (1994)
- The Godfather (1972)
- The Godfather: Part II (1974)
- The Dark Knight (2008)
- 12 Angry Men (1957)
- Schindler's List (1993)
- The Lord of the Rings: The Return of the King (2003)
- Pulp Fiction (1994)
- The Good, the Bad and the Ugly (1966)
- The Lord of the Rings: The Fellowship of the Ring (2001)
Your request has been completed. Is there anything else I can help you with today?
ME: I want to buy movie tickets
Bot: Oh sure, I’d be happy to help you book movie tickets at Old Movie Theater. Which movie do you want to see?
Your choices are listed here:
- The Shawshank Redemption (1994)
- The Godfather (1972)
- The Godfather: Part II (1974)
- The Dark Knight (2008)
- 12 Angry Men (1957)
- Schindler's List (1993)
- The Lord of the Rings: The Return of the King (2003)
- Pulp Fiction (1994)
- The Good, the Bad and the Ugly (1966)
- The Lord of the Rings: The Fellowship of the Ring (2001)
ME: The Godfather, please
BOT: Great choice! What date do you prefer?
ME: tomorrow
BOT: Got it. And what time?
Your choices are listed here:
- 10:00 AM
- 12:30 PM
- 3:00 PM
- 5:30 PM
- 8:00 PM
ME: 3pm
BOT: Got it. How many tickets do you want to buy?
ME: 2 tickets
BOT: All set. I booked your tickets. I look forward to seeing you at Old Movie Theater. Is there anything else I can help you with today?
ME: where do I park my car?
BOT: Convenient, free guest parking is located next to the theater. The entrance to the 7-story parking garage is off California Street, past the front of the theater. Is there anything else I can help you with today?
ME: no. thank you
BOT: Sounds good. I'm glad I could help. Thanks for calling, and have a good one.
```

## Online banking
```yaml
Task:
  verify_user:
    description: verify your identity
    samples: []
    entities:
      name:
        function: get_name_and_welcome
        confirm: false
        prompt:
          - What's your name?
        response:
          - <info>.
      card_number:
        function: verify_credit_card
        confirm: false
        prompt:
          - May I have your credit card number?
        response: []
      zip_code:
        function: verify_zip_code
        confirm: false
        prompt:
          - Could you please confirm the zip code of your primary address?
        response: []
    entity_groups:
      identity_group:
        - name
        - card_number
        - zip_code
    success:
      AND:
        - VERIFY:
            - identity_group
    finish_response:
      success:
        - Perfect. I pulled up your account.
      failure:
        - Sorry, I am not able to verify your identity.
    repeat: false
    repeat_response: []
    task_finish_function: null
    max_turns: 10
  credit_card_not_working:
    description: resolve your credit card issues
    samples:
      - my credit card is not working
      - my credit card does not go through
      - I am not able to make payments using my credit card
    entities:
      reason:
        function: inform_the_credit_card_issue
        confirm: false
        prompt: []
        response:
          - <info>
    entity_groups:
      reason_group:
        - reason
    success:
      AND:
        - TASK:
            - verify_user
        - INFORM:
            - reason_group
    finish_response:
      success: []
      failure: []
    repeat: false
    repeat_response: []
    task_finish_function: null
    max_turns: 15
  check_balance:
    description: check your credit card balance
    samples:
      - what is the balance that I need to pay?
      - how much do I need to pay?
      - what is the current balance
      - check the balance
    entities:
      remaining_balance:
        function: get_remaining_balance
        confirm: false
        prompt: []
        response:
          - <info>
    entity_groups:
      balance_due_group:
        - remaining_balance
    success:
      AND:
        - TASK:
            - verify_user
        - INFORM:
            - balance_due_group
    finish_response:
      success: []
      failure: []
    repeat: false
    repeat_response: []
    task_finish_function: null
    max_turns: 10
```
There are 3 tasks in this online banking bot. `verify_user` is a sub-task, which is shared by `credit_card_not_working` and 
`check_balance`. The `credit_card_not_working` task will help users with their credit card issues and tell users why their
credit cards are not working. `check_balance` will help users check the remaining balance due of their credit cards.

An example conversation between this bot and the user is below:
```
BOT: Hi there, I am the digital assistant for berich bank. What can I do for you?
ME: my credit card is not working
BOT: Oh sure, I’d be happy to help you resolve your credit card issues. First, I need to verify your identity. What’s your name?
ME: My name is Peter Parker
BOT: Hi, Peter. May I have your credit card number?
ME: It is 4000000000000000
BOT: Got it. Could you please confirm the zip code of your primary address?
ME: 95100
BOT: Okay. Perfect. I pulled up your account. It seems that your credit card has been suspended because your balance has not been paid for 3 months. We will re-activate your credit card as soon as we receive the payment in full. Your request has been completed. Is there anything else I can help you with today?
ME: how much do I need to pay?
BOT: Your balance due is $250.13. Your request has been completed. Is there anything else I can help you with today?
ME: no. thank you
BOT: Sounds good. I’m glad I could help. Thanks for calling, and have a good one.
```

## Customize a T-shirt
```yaml
Task:
  customize_tshirt:
    description: customize your T-shirts
    samples:
      - I want to order T-shirts.
      - I want to order a shirt.
      - I want to customize a t shirt.
      - can I customize tshirt?
      - order tshirts
    entities:
      color:
        function: collect_info
        confirm: false
        prompt:
          - Which color do you prefer?
        response:
          - Wonderful choice.
      size:
        function: collect_info
        confirm: false
        prompt:
          - What size do you want?
        response:
          - Great!
      front_text:
        function: collect_info
        confirm: false
        prompt:
          - What text do you want to print on the front side of the T-shirt?
        response:
          - Got it.
      back_text:
        function: collect_info
        confirm: false
        prompt:
          - What text do you want to print on the back side?
        response:
          - OK.
    entity_groups:
      color_size_group:
        - color
        - size
      front_text_group:
        - front_text
      back_text_group:
        - back_text
    success:
      AND:
        - API:
            - front_text_group
        - API:
            - back_text_group
        - API:
            - color_size_group
    finish_response:
      success:
        - <info>
      failure: []
    repeat: false
    repeat_response: []
    task_finish_function: finish_order_tshirts
    max_turns: 10
  change_color:
    description: change the shirt color
    samples:
      - I want to change the shirt color
      - change it to color
      - change the color to color
      - the color is too bright
      - can I change the color
    entities:
      color:
        function: collect_info
        confirm: false
        prompt:
          - What do you want the new color to be?
        response:
          - Definitely. I have changed the color.
        forget: true
    entity_groups:
      color_group:
        - color
    success:
      AND:
        - TASK:
            - customize_tshirt
        - API:
            - color_group
    finish_response:
      success:
        - <info>
      failure: []
    repeat: false
    repeat_response: []
    task_finish_function: finish_order_tshirts
    max_turns: 10
FAQ:
  unisex:
    samples:
      - Is it unisex?
      - Is the T-shirt unisex?
      - Is the shirt unisex?
    answers:
      - Yes, it is unisex.
    question_match_options:
      - fuzzy_matching
      - nli
```
This bot is an example for manufacturing scenario. There are two tasks, `customize_tshirt` and `change_color`. `customize_tshirt` 
is the main task in this bot. When users want to customize a T-shirt, a required entity is the color of the T-shirt. If you want 
the users to be able to change their mind after they provide information for an entity, you need to create a task to do this.
`change_color` is an example for this scenario. Currently, users are not able to change the value of an entity when it is 
already collected/ processed without a task like the `change_color` example.

There's also an FAQ in this bot. Users can ask the bot whether the T-shirt is unisex.

An example conversation between this bot and the user is below:
```
BOT: Hi there, I am the digital assistant for Ushirt Factory. What can I do for you?
ME: hi, I want to order T-shirts
BOT: Oh sure, I’d be happy to help you customize your T-shirts. What text do you want to print on the front side of the T-shirt?
ME: nothing
BOT: Got it. What text do you want to print on the back side?
ME: “Big Brain”
BOT: OK. Which color do you prefer?
Your choices are listed here:
- white
- black
- red
- pink
- yellow
- blue
- purple
ME: pink sounds great
BOT: Wonderful choice. What size do you want?
Your choices are listed here:
- small
- medium
- large
- extra large
ME: Is it unisex?
BOT: Yes, it is unisex. Wonderful choice. What size do you want?
Your choices are listed here:
- small
- medium
- large
- extra large
ME: I prefer medium size
BOT: Great! A pink medium T-shirt with nothing on the front side and “Big Brain” on the back side. Your order is submitted. Thank you! Is there anything else I can help you with today?
ME: can I change the color?
BOT: Oh sure, I’d be happy to help you change the shirt color. What do you want the new color to be?
Your choices are listed here:
- white
- black
- red
- pink
- yellow
- blue
- purple
ME: I want purple.
BOT: Definitely. I have changed the color. A purple medium T-shirt with nothing on the front side and “Big Brain” on the back side. Your order is submitted. Thank you! Is there anything else I can help you with today?
ME: no. thank you!
BOT: Sounds good. I’m glad I could help. Thanks for calling, and have a good one.
```

## Book a flight
```yaml
Task:
  book_a_flight:
    description: book a flight
    samples:
      - book a flight
      - I would like to book a flight
      - I want to book a flight from somewhere to somewhere
      - book flight from somewhere to somewhere
    entities:
      origin:
        function: collect_info
        confirm: no
        prompt:
          - What is the origin of your trip?
      destination:
        function: collect_info
        confirm: no
        retrieve: False
        prompt:
          - What is the destination of your trip?
      start_date:
        function: collect_info
        confirm: no
        prompt:
          - When will your trip start?
      end_date:
        function: collect_info
        confirm: no
        retrieve: False
        prompt:
          - When will your trip end?
      passenger_num:
        function: collect_info
        confirm: no
        prompt:
          - How many passengers?
      fare_class:
        function: collect_info
        confirm: no
        prompt:
          - And which fare class? (e.g., Economy, Business, First)
      flight_info_departing:
        function: search_departuring_flight
        confirm: no
        prompt:
        response:
          - <info>
      flight_choice_departing:
        function: choose_flight_departing
        confirm: no
        prompt:
          - Which one do you prefer?
        response:
          - <info>
      flight_info_returning:
        function: search_returning_flight
        confirm: no
        prompt:
        response:
          - <info>
      flight_choice_returning:
        function: choose_flight_returning
        confirm: no
        prompt:
          - Which one do you prefer?
        response:
          - <info>
    entity_groups:
      origin_group:
        - origin
      destination_group:
        - destination
      start_date_group:
        - start_date
      end_date_group:
        - end_date
      passenger_num_group:
        - passenger_num
      fare_class_group:
        - fare_class
      flight_info_departing_group:
        - flight_info_departing
      flight_choice_departing_group:
        - flight_choice_departing
      flight_info_returning_group:
        - flight_info_returning
      flight_choice_returning_group:
        - flight_choice_returning
    success:
      AND:
        - INSERT:
            - origin_group
        - INSERT:
            - destination_group
        - INSERT:
            - start_date_group
        - INSERT:
            - end_date_group
        - INSERT:
            - passenger_num_group
        - INSERT:
            - fare_class_group
        - INFORM:
            - flight_info_departing_group
        - INSERT:
            - flight_choice_departing_group
        - INFORM:
            - flight_info_returning_group
        - INSERT:
            - flight_choice_returning_group
    finish_response:
      success:
        - OK, I'm going to connect you to an agent to process the credit card for privacy reasons. One moment, please.
      failure:
        - Sorry, I cannot help you to find a flight. I'm going to connect you to an agent. One moment, please.
    repeat: false
    max_turns: 30

FAQ:
  learn_about_salesforce_AI_research:
    samples:
      - Could you tell me about the Salesforce AI research team?
      - tell me about Salesforce AI research team
      - what projects does the salesforce AI research team work on?
      - what projects are salesforce researchers working on?
      - I would like to know more about Salesforce research projects
    answers:
      - OK, here's what I found - https://einstein.ai/mission.
    question_match_options:
      - fuzzy_matching
      - nli
  job:
    samples:
      - where can I find job opportunities in Salesforce research?
    answers:
      - Thanks for your interest! Please see https://einstein.ai/career.
    question_match_options:
      - fuzzy_matching
  compliment:
    samples:
      - You are amazing!
    answers:
      - Thanks! I'm flattered :)
    question_match_options:
      - fuzzy_matching
```
The flight booking bot has 1 task, `book_a_flight`. The `book_a_flight` task collects necessary information for booking a 
flight, and helps users to search and choose flights.

There are also some FAQs in this bot. They are not quite relevant to booking flights. We use them as examples of small 
talk.

An example conversation between this bot and the user is below:
```
BOT: Hi there, I am Converse demo bot. What can I do for you?
ME: I’d like to book a round-trip flight
BOT: Oh sure, I’d be happy to help you book a flight. What is the origin of your trip?
ME: From San Francisco to Los Angeles for 2 people
BOT: I got multiple possible answers for origin, San Francisco and Los Angeles, which one did you mean? Could you walk me through the details?
ME: San Francisco
BOT: Okay. What is the destination of your trip?
ME: Los Angeles
BOT: Okay. When will your trip start?
ME: tomorrow
BOT: Okay. When will your trip end?
ME: next Monday
BOT: Got it. Your passenger num is 2. Is that correct?
ME: yes
BOT: Got it. And which fare class? (e.g., Economy, Business, First)
ME: economy please
BOT: Got it. Let’s start with your departing flight. Here are the cheapest flights from San Francisco to Los Angeles on 2021-12-09:
Oceanic 815, Depart at 4:16am, 800USD
Ajira 316, Depart at 15:42pm, 1500USD
Qantas 442, Depart at 23:08pm, 2300USD. Which one do you prefer?
ME: the first one please
BOT: Your departing flight is Oceanic 815. And here are your returning flights: 
Oceanic 443, Depart at 4:16am, 800USD
Ajira 232, Depart at 15:42pm, 1500USD
Qantas 424, Depart at 23:08pm, 2300USD. Which one do you prefer?
ME: Ajira
BOT: Alright, your return flight is Ajira 232. OK, I'm going to connect you to an agent to process the credit card for privacy reasons. One moment, please. Can I assist you with anything else?
ME: no. thank you!
BOT: Thanks for taking the time to chat!
```