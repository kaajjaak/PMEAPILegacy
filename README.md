
# Productivity Made Easy

A Python FastAPI program made for the Productivity Made Easy project.


## Information

I originally made this as my final project to graduate from highschool. This project was very rushed, though this version, the API, is fully functional but has a bunch of issues that will be discussed later on in this document, if these issues were addressed, this would be a great and usable API, however for the rewrite I decided to go with a completely different tech stack so I will therefore not be fixing them.

The API used to be hosted for free on Heroku but they currently do not offer the free tier anymore so the API is therefore offline. The MySQL database hosting itself was provided by my highschool which I now graduated from and is therefore also offline.

## Rewrite

I'm currently working on a complete rewrite of the project since I do believe this project had a lot of potential that it has not yet reached. It will be a very different tech stack so this repository will therefore not be updated but I will link the new project once I have a public repository for it.


## Disclaimer

As mentioned before, this project has a lot of critical errors that I only realise now that I have more experience in the field.

There are a couple big issues with this API which I will list here.
1. I first learned about JWT tokens from a chat application called Discord, the way Discord implements is completely wrong but since I copied their implementation, mine is completely wrong too since I didn't understand how they were actually used to begin with.
	- A copy of the token is stored in the database, on each request this token will be compared with the token the user sends.
	- Tokens never expire, not over time and not even upon a password reset, if a user's token gets stolen, there is no way to lock out the hacker since you can do everything using just the token.
	- The tokens are not readable through [JWT Website](https://jwt.io/) since they are encryped.
		- They are encrypted because the original user password is stored inside of them, which is also horrible OPSEC.
2. I did not understand how passwords are stored in databases since we just stored them in cleartext when making exercises during class (though we never learned how to make an API to begin with)
	- The passwords are encrypted instead of hashed.
		- If a hacker were to get access to the encryption/decryption key (it uses symmetric encryption) and the database itself, they would easily be able to decrypt all the passwords and get them in cleartext.
		- Me (the developer) would be able to decrypt the passwords as well which is not really user friendly.
	- Passwords aren't salted
	- I implemented too much of the password process myself in general which is a bad idea if you have no experience with it, it is generally recommended to use password specific libraries.
	- In my defense, my unorthodox way of implementing password encryption instead of hashing means that a hacker would never be able to use a rainbow table to decrypt the entire database, though a proper implementation of salting solves the same issue and better.
3. All secrets and passwords are not saved in a `.env` file and instead just in the `main.py` file. This was somewhat fine during production since it was a private repo only for myself but it is generally still recommended to store secret information in a different file which would then be added to `.gitignore` just in case. If not for security reasons, this is also better if you want to expand the project to multiple files.
4. There are some more small issues such as imports from previous versions which are now unused and the test file being commited and therefore also pushed to heroku iirc but I think I have listed enough.
5. It uses post requests for everything since it didn't want to work in C# otherwise. I'm not entirely sure how big of a deal this is.

I was originally considering reusing this API for the complete rewrite in a way where I would address all these issues but after some thinking, I decided not to do that and just writing a new API in a more commonly used API framework.

 
## Related

- [Legacy Desktop Version](https://github.com/kaajjaak/PMEDesktopLegacy)
- [Legacy Mobile Version](https://github.com/kaajjaak/PMEMobileLegacy)
- [Legacy Android Version (unfinished)](https://github.com/kaajjaak/PMEAndroidLegacy)



## Author

- [@Akina](https://www.github.com/kaajjaak)

