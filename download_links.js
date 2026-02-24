// download_links.js
// Base de données des liens et descriptions SEO

const productData = {
    // LOGIC
    "Tic Tac Toe": {
        link: "https://drive.google.com/uc?export=download&id=1sLEHa4hVNhslv_fMlBpwJglPqjTr7Ml-",
        desc: "A classic strategy game that helps children develop critical thinking and sportsmanship skills."
    },
    "Tic Tac Logic": {
        link: "https://drive.google.com/uc?export=download&id=1q5IV1sr6boFx-qncyx-2zUGZCzXqJcdf",
        desc: "A step up from the classic! This puzzle challenges spatial reasoning and logic planning."
    },
    "Nurikabe": {
        link: "https://drive.google.com/uc?export=download&id=1yA6hqRGsqXviBHtNMdBZkgmXgdVXgoUQ",
        desc: "A Japanese logic puzzle forming islands. Excellent for developing concentration and patience."
    },
    "Hitori": {
        link: "https://drive.google.com/uc?export=download&id=14_Y0LCX51aDYUZIybjSORMZIIudmikWj",
        desc: "Eliminate duplicate numbers in this engaging grid puzzle. Perfect for math logic practice."
    },
    "Kakurasu": {
        link: "https://drive.google.com/uc?export=download&id=1V1MtGt_gOCP58OS_rGIhlq68xRerYVfm",
        desc: "Combine logic and addition sums in this unique puzzle. Great for strengthening mental math."
    },
    "Shikaku": {
        link: "https://drive.google.com/uc?export=download&id=1JfjM0sOj6fK30fmzFRtCKy3hZGidOWVx",
        desc: "Divide the grid into rectangles. A fantastic visual-spatial geometry exercise for kids."
    },
    "Four In A Row": {
        link: "https://drive.google.com/uc?export=download&id=1KgY8T7Y45zUCa0PQy1h0gKDKgnPO85Pb",
        desc: "Connect four pieces to win. Builds strategic forward-thinking and pattern recognition."
    },
    "Skyscraper": {
        link: "https://drive.google.com/uc?export=download&id=1Si2HCW7TI46ALGZ00iPnp0bn28bbNdG1",
        desc: "Build a city skyline using logic. A fun twist on Sudoku that kids love."
    },
    "Mine Finder": {
        link: "https://drive.google.com/uc?export=download&id=1Aa3v8jSlt1zZCQX996KMT874KtuQrx4E",
        desc: "Clear the grid without detonating mines. Teaches risk assessment and deductive reasoning."
    },
    "Warships": {
        link: "https://drive.google.com/uc?export=download&id=1eoLfCNkbrpNkUn1yLpwAc6UC1nwHd90f",
        desc: "Locate the hidden fleet. A classic game of deduction and coordinate tracking."
    },
    "Logic Puzzle (Adult)": {
        link: "https://drive.google.com/uc?export=download&id=1RqBwqNktyLq4LpGdzWYV7mkX6jvA5Wou",
        desc: "Advanced logic grids for older students and adults to keep the mind sharp."
    },

    // WORDS
    "ABC Path": {
        link: "https://drive.google.com/uc?export=download&id=1fP3wwtHPJHeUa4SQbf_PJqUJACsONVYx",
        desc: "Trace the alphabet through the grid. Reinforces letter sequencing and pathfinding."
    },
    "Hangman": {
        link: "https://drive.google.com/uc?export=download&id=1qvvb77Gxp6iUtcKtmTu365MpuZAvg2tU",
        desc: "Guess the word before it's too late! Expands vocabulary and spelling skills."
    },
    "Word Search": {
        link: "https://drive.google.com/uc?export=download&id=1jkLi6Wpv3fq7KZbQTBIV_-1U2Yge3LMl",
        desc: "Find hidden words in the grid. Improves pattern recognition and vocabulary."
    },
    "Crossword": {
        link: "https://drive.google.com/uc?export=download&id=1VyLYHAPtmvoGGnw0Ts-E7KKl2qw1HM72",
        desc: "Solve clues to fill the grid. The ultimate test of general knowledge and spelling."
    },
    "Missing Vowels": {
        link: "https://drive.google.com/uc?export=download&id=1qKWXAuCpczgeI3Qkqn5XU2zmnL2RuixW",
        desc: "Fill in the missing vowels to complete words. Great for phonics and reading fluency."
    },
    "Word Scramble": {
        link: "https://drive.google.com/uc?export=download&id=1qwX7X0Fih8EnNbvDVV0WpVqMKqcNBhmF",
        desc: "Unscramble the letters to reveal words. Boosts spelling and cognitive flexibility."
    },
    "Cryptogram": {
        link: "https://drive.google.com/uc?export=download&id=1I-oUCstYz-0tcRFAtEyZcLd64xrcMHCw",
        desc: "Decode the secret message. A fun introduction to codes and ciphers."
    },
    "Complete the Word": {
        link: "https://drive.google.com/uc?export=download&id=1O_-kEScVVgl41EIiPZN2pILqsFL7EXAU",
        desc: "Finish the partial words. Helps with vocabulary recall and spelling confidence."
    },
    "Spot Correct Spelling": {
        link: "https://drive.google.com/uc?export=download&id=18svQ97GBrcdCx82RORGu982EJzTajhx8",
        desc: "Identify the correctly spelled word. Essential practice for standardized tests."
    },
    "Bi-Lingual Matching": {
        link: "https://drive.google.com/uc?export=download&id=1IJxeHu1bAadhFZa9qR-lZAmqsiIyM9ku",
        desc: "Match words across two languages. Perfect for ESL students and language learners."
    },

    // MATH
    "Sudoku": {
        link: "https://drive.google.com/uc?export=download&id=1kMsX9yB_YhSkC_isuQoo_8Lg8JZfwgld",
        desc: "The classic number placement puzzle. Builds pure logic and deductive skills."
    },
    "CalcuDoku": {
        link: "https://drive.google.com/uc?export=download&id=17bIZJ3tBbh3u_NvVVABsRut57H5dohzA",
        desc: "Sudoku meets math operations. Fun way to practice addition, subtraction, multiplication, and division."
    },
    "Kids Math Equations": {
        link: "https://drive.google.com/uc?export=download&id=1PjoEBsMxS_eSW-H4Uql_wKv9IrOJfQUD",
        desc: "Solve the equations to clear the board. Direct practice for arithmetic fluency."
    },
    "Counting Numbers": {
        link: "https://drive.google.com/uc?export=download&id=1hodAjxXzxzrjuijnsphu7jIowu2lN46t",
        desc: "Fun counting exercises for early learners to build number sense."
    },
    "Range Puzzle": {
        link: "https://drive.google.com/uc?export=download&id=1jUnHqtq-y5roFYBSb4y5hw40FjF_QMfM",
        desc: "Determine the range and placement of numbers. Advanced logical thinking for math."
    },
    "One Hundred Puzzle": {
        link: "https://drive.google.com/uc?export=download&id=1BKcqK7IOmrWZd4nZRbBShba0Mduhb_8-",
        desc: "Work with the 100-chart to find patterns. Essential for understanding number relationships."
    },

    // CREATIVE
    "Stickers Pack": {
        link: "https://drive.google.com/uc?export=download&id=1xqBtCb6QPID7MmTzfcJBiGmyXalMECNk",
        desc: "Printable stickers for rewards and decoration. Adds fun to any notebook!"
    },
    "Clip Art Set": {
        link: "https://drive.google.com/uc?export=download&id=1hCOsB-cX81kqsD1BMxHAoANBhhjiSzLk",
        desc: "High-quality clipart for student projects and classroom decorations."
    },
    "Coloring Page (Kids)": {
        link: "https://drive.google.com/uc?export=download&id=1WuFF1fYLt6ah2Xgcd_Y-wOMprrunC473",
        desc: "Engaging illustrations to color. Improves fine motor skills and creativity."
    },
    "Coloring Page (Adult)": {
        link: "https://drive.google.com/uc?export=download&id=12UpsVEr0vrbGMkd5bS156F_zyVM36M3b",
        desc: "Intricate designs for relaxation and mindfulness. Take a break and create art."
    },
    "Cookbook for Kids": {
        link: "https://drive.google.com/uc?export=download&id=1iCIyaTwdiOCZi5ZyWuSQsH_bRrbjg-kR",
        desc: "Simple, safe recipes for young chefs. Teaches following instructions and measurements."
    },
    "Joke Book for Kids": {
        link: "https://drive.google.com/uc?export=download&id=1Isik52YmevUpuueZJobQKkylU9TIOY0n",
        desc: "Clean, funny jokes to keep the classroom laughing. Great for reading practice."
    },
    "Activity Book": {
        link: "https://drive.google.com/uc?export=download&id=1CvIBdbWc9rn4wa65i5N5yvxBCgLxNeB8",
        desc: "A mixed collection of puzzles and games. Perfect for road trips or rainy days."
    },
    "Spot the Difference": {
        link: "https://drive.google.com/uc?export=download&id=1mJatCxHXsG_LbVAUyHcvuGbhpNTuuPLJ",
        desc: "Find the subtle differences between images. Sharps observation and attention to detail."
    },
    "Shadow Matching": {
        link: "https://drive.google.com/uc?export=download&id=12920MbVWqFsKN7PQbtRJlnQ2N2aStW2z",
        desc: "Match the object to its shadow. A critical pre-reading visual discrimination skill."
    },
    "Maze for Kids": {
        link: "https://drive.google.com/uc?export=download&id=16TVMRA-ynjzluisizspL2Gy7mWNCxwPU",
        desc: "Navigate the labyrinth to the exit. Develops problem-solving and pen control."
    },

    // PACKS (Ces liens sont des placeholders, à remplacer par vos vrais ZIP)
    "Full Freebie Pack": {
        link: "https://drive.google.com/uc?export=download&id=1Gdvmp2gBTbj_194tN5SXHN68IKhODZgu",
        desc: "The complete collection of all our current free resources in one click."
    },
    "Creative Pack": {
        link: "https://drive.google.com/uc?export=download&id=1dTue-BzNZ08s9ndIVT59QQhCXwPz-GM9",
        desc: "A bundle of all art, coloring, and creative activities."
    },
    "Logic Pack": {
        link: "https://drive.google.com/uc?export=download&id=17GU3eZUUvpPoDbJnSaNavoRfUWUBWWbX",
        desc: "A bundle of all logic grids and strategy puzzles."
    },
    "Math Pack": {
        link: "https://drive.google.com/uc?export=download&id=1FnMwDNyxKiwkHak7aqAiIW_-Jmz9bqsh",
        desc: "A bundle of all numerical and arithmetic puzzles."
    },
    "Word Pack": {
        link: "https://drive.google.com/uc?export=download&id=1zIROJhLpbo3iNQ_MlkccV_RmadtwnMTo",
        desc: "A bundle of all vocabulary and spelling games."
    }
};