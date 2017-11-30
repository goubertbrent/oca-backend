# GOAL

In the news stream the news articles sent by the community services are sinking under the news articles sent by merchant/association/care services.

# Description

We want to change the news article priorities such that news articles sent by community services are displayed higher than those of merchant/association/care services.

_In the ideal world the new sort priorities should be:_
1. `(05)` _News articles sent by community services_
2. `(10)` _Sponsored news articles_
3. `(20)` _News articles liked by friends_
4. `(30)` _News articles sent by connected services_
5. `(40)` _News articles sent by other services_
6. `(45)` _News articles that don't match the target audience_
7. `(50)` _Read news articles_

However, we're taking a shortcut and will give case 1 and 2 the same priority. This will only take 1 minute to implement. We'll evaluate later. If we need to roll it back it will also take only 1 minute.

1. `(10)` News articles sent by community services or sponsored news articles
2. `(20)` News articles liked by friends
3. `(30)` News articles sent by connected services
4. `(40)` News articles sent by other services
5. `(45)` News articles that don't match the target audience
6. `(50)` Read news articles

# Implementation

When calling `news.publish` set `sticky=True` if the organization type of the service/customer is COMMUNITY_SERVICE.

### Remarks

We should not use these priorities in apps with custom organization types (like ae-veda)
