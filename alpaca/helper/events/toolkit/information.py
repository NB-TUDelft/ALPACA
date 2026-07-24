from display import display
from version import ALPACA_FW_VER
import random 

SCROLL_DELAY_MS = 300 

ORIGINAL_TEXT = random.choice([
"ALPACA fiber is known for being hypoallergenic because it does not contain lanolin.",
"ALPACA herds use a communal dung pile to keep their grazing areas clean.",
"ALPACA vocalizations include a soft humming sound to communicate with the herd.",
"ALPACA fleece comes in 22 natural shades recognized in the textile industry.",
"ALPACA stomach anatomy includes three compartments to maximize nutrient absorption.",
"ALPACA ears are distinctly spear-shaped and swivel to detect movement.",
"ALPACA gestation lasts approximately 11 to 12 months.",
"ALPACA newborns are referred to as crias.",
"ALPACA grazing behavior involves clipping grass rather than pulling it up by the roots.",
"ALPACA social structure relies on a strong hierarchical system.",
"ALPACA teeth continue to grow throughout their lives and require wear from forage.",
"ALPACA history traces back to the high Andes of South America.",
"ALPACA wool is naturally water-repellent and flame-resistant.",
"ALPACA spitting is a defensive mechanism usually directed at other herd members.",
"ALPACA physical size varies significantly between the two breeds, Huacaya and Suri.",
"ALPACA feet are padded, making them gentle on pastures compared to hooved animals.",
"ALPACA breeding is induced, meaning the female ovulates upon stimulation.",
"ALPACA temperature regulation is assisted by the high thermal insulation of their coat.",
"ALPACA intelligence allows them to be halter-trained with consistency.",
"ALPACA populations have increased globally due to the demand for their luxury fiber.",
"ALPACA communication includes a high-pitched 'alarm call' when sensing danger.",
"ALPACA life expectancy is typically between 15 and 20 years.",
"ALPACA fiber diameter is measured in microns to determine its quality grade.",
"ALPACA shearers typically harvest fiber once per year, usually in the spring.",
"ALPACA defense mechanisms include chasing or kicking potential predators.",
"ALPACA survival in extreme altitudes is due to their highly efficient oxygen-carrying blood.",
"ALPACA dominance is often established through neck wrestling or 'spitting matches'.",
"ALPACA colors range from stark white to jet black and various shades of brown.",
"ALPACA grooming involves 'dust bathing' to remove loose debris and parasites.",
"ALPACA ears are expressive and signal mood, with flat ears indicating annoyance.",
"ALPACA weight for an adult typically ranges between 100 and 190 pounds.",
"ALPACA wool is considered warmer than sheep’s wool due to its medullated fibers.",
"ALPACA herds often include other livestock like llamas or sheep for protection.",
"ALPACA health is monitored by checking the color of the mucous membranes.",
"ALPACA fiber was highly prized by the Inca civilization as the 'fiber of the gods'.",
"ALPACA milk is exceptionally rich, supporting rapid growth in the first few months.",
"ALPACA behavior includes 'pronking', a joyful jumping motion used during play.",
"ALPACA ears serve as a primary indicator of where the animal is focusing its attention.",
"ALPACA domestication occurred approximately 6,000 years ago.",
"ALPACA fiber quality can be assessed through histogram testing for fineness.",
"ALPACA grazing patterns are often rotational to maintain pasture health.",
"ALPACA height at the withers is usually around 3 feet tall.",
"ALPACA fleece is virtually free of vegetable matter due to their cleanliness.",
"ALPACA social bonds are very strong, and they can become stressed if isolated.",
"ALPACA ears are often used to identify individual animals from a distance.",
"ALPACA fiber has a smooth scale structure, which results in a soft, non-itchy feel.",
"ALPACA birth usually occurs during daylight hours in the Andes to avoid cold nights.",
"ALPACA fiber strength is high, allowing for durable garments.",
"ALPACA interaction with humans requires respect for their space to avoid over-familiarity.",
"ALPACA farming is considered a sustainable agricultural practice."
])

PADDED_TEXT = " " * 8 + ORIGINAL_TEXT + " " * 8
TEXT_LEN = len(PADDED_TEXT)

def display_info(last_tick):
  steps = int(last_tick / SCROLL_DELAY_MS)
  
  start_i = steps % (TEXT_LEN - 8)
  end_i = start_i + 8
  
  scrolling_text = PADDED_TEXT[start_i:end_i]
  
  display.set_text(scrolling_text, f"FW-{ALPACA_FW_VER}")
