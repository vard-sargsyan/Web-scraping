# Web-scraping
Some of my web scraping codes

Often an information you need is right there on the web. But do you have all time and nerves to manually search, browse, copy, and paste all those pages and listings over and over? I don't, that's why I love data scraping. In fact, my first attempts of to read and understand Python were triggered by my desire to scrap web data.

In this repository, I keep some of my web scraping codes, which (at least at the time of posting) allow fully automated scraping of the corresponding websites and writing the structured data into Excel file (can be any other suitable format). So, here they are:

Listam_RE_parser_BS.py
----------------------
list.am is a popular announcement portal in Armenia. It's the most used one so far with many times more announcements than in all other resources combined. That's why we have to use it despite it's low quality and lack of structure. After the last time I search for an apartment to rent on list.am I promised I'll never go through that headache again. Hence, I developed this scraper so that I don't end up homeless should I need to move out from my current place :)

It's very flexible and allows scraping all the real estate categories (house/apartment for rent or sale, business locations, land, etc.) with any filtering you wish. And customizing it for any other category on the portal (like cars, services, etc.) will take just minutes.

By the way, that's not all. As the portal has a lot of problems like incomplete addresses, repeated announcements and poor geodata, scraping it was only the first step. Stay tuned for more fun codes to refine and geotag addresses, filter out repeat ads and discover fake announcements.


Listam_RE_parser_Se.py
----------------------
This one is the first version for the same list.am website. At that time I still didn't know that just by adjusting headers in the request I can access pages that block automated crawling :) So I did it with Selenium designing it as a real user browsing. Of course, this is much slower than the above version with Requests and BeautifulSoup, but it was still a good experience and a learning opportunity.

EIF_IT_database.py
------------------
EIF or Enterprise Incubator Foundation has a database of Armenian IT companies that I was keen to have myself at the time. My steps? Scrape it!


EIF_Engineering_database.py
---------------------------
In fact, EIF had to databases - one for IT, and one for engineering companies - and I needed both. Their pages looked very similar and I was sure I'll scrape the second one with the code I had just by changing the url... but nope. There was a trick and I had to revise the code to send a POST request instead of the standar GET. Right now the two codes look very similar except that one line, but boy, was it a challenge for me to figure out how to make it work at the time cus it wasn't obvious from the page! That's why I kind of feel this baby is also worth posting.

So, this is it for now. But, as already noted, I love scraping and I'm gonna keep on doing it. So more fun stuff is coming!
