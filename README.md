# Scientific article organizer

I'm thinking of some sort of system that can facilitate reading new articles, I was thinking of like it giving me some random new articles from arxiv

Show 10(?) articles from the past day in the chosen category, w/ details, with a number beside. user hits that number to see more details (full abstract) and some options like downloading the pdf and stuff.
Can change query terms like category, sort, etc on the fly

### Ex:

[1] **On the black hole content and initial mass function of 47 Tuc**
{dim} V. Hénault-Brunet; M. Gieles; J. Strader; M. Peuten; E. Balbinot; K.E.K. Douglas {\dim}

    The globular cluster (GC) 47 Tuc has recently been proposed to host an intermediate-mass black hole (IMBH) or a population of stellar-mass black holes (BHs). To shed light on its dark content, we present an application of self-consistent multimass models with a varying mass function and content of stellar remnants, which we fit to various observational constraints. Our best-fitting model successfu...

[2] ......

### options

- full author list or just main et al.
- abstract character count cut-off (or full)
- download pdf or read online


### Notes

- "Because the arXiv submission process works on a 24 hour submission cycle, new articles are only available to the API on the midnight after the articles were processed. The <updated> tag thus reflects the midnight of the day that you are calling the API. This is very important - search results do not change until new articles are added. Therefore there is no need to call the API more than once in a day for the same query. Please cache your results. This primarily applies to production systems, and of course you are free to play around with the API while you are developing your program!"
    + thats why querying isn't showing the same as the webpage results.
- However, using just cat:astro-ph with "submittedDate" doesn't seem to be working at all (article is from 2019?) (using updatedDate might be working however? but thats less useful I think)