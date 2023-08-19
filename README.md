<div align="center">

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]

</div>

<br />
<div align="center">
  <h3 align="center">PySilpo</h3>

  <p align="center">
    <b>UNOFFICIAL</b> API client for Silpo (Ukrainian supermarket chain)
    <br />
    <br />
    <a href="https://github.com/iYasha/pysilpo/issues">Report Bug</a>
    ·
    <a href="https://github.com/iYasha/pysilpo/issues">Request Feature</a>
  </p>
</div>

## Installation

Use the package manager pip to install PySilpo.

```bash
pip install pysilpo 
```

## Usage

The library needs to be configured with your account access token, 
which you can get from [Silpo](https://silpo.ua/).
1. Login to your account
2. Open developer tools in your browser
3. Go to `Console` tab
4. Execute this script
```javascript
const value = `; ${document.cookie}`;
const parts = value.split(`; accessToken=`);
if (parts.length === 2)
    console.log("%c" + parts.pop().split(';').shift(), "font-size: 20px; color: green;");
else
    console.log("%cAccess token not found. Please make sure that you Logged in your account!", "font-size: 20px; color: red;")
```
5. Copy the output and use it as access token

<i>Access token live only <b>90</b> days.</i>

```python
import pysilpo
from pysilpo.client import APIClient
from datetime import datetime

pysilpo.api_key = "NDSyYmDwMHE5ODE0Z2JhYTU3HzQ3YzU5YjG2OTRjYTg"

cheques = APIClient.fetch_cheques(
    date_from=datetime(2023, 7, 19),
    date_to=datetime(2023, 8, 19),
).get()

print(cheques)
```

## Change Log

### 0.0.1
- Initial release
- Added support for new resource `Cheque History`, `Cheque Detail` and `User Info`
- Added `README.md` file

## Contributing
Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Contact
If you have any questions, feel free to contact me via email: [ivan@simantiev.com](mailto:ivan@simantiev.com)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/iyasha/pysilpo.svg?style=for-the-badge
[contributors-url]: https://github.com/iyasha/pysilpo/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/iyasha/pysilpo.svg?style=for-the-badge
[forks-url]: https://github.com/iyasha/pysilpo/network/members
[stars-shield]: https://img.shields.io/github/stars/iyasha/pysilpo.svg?style=for-the-badge
[stars-url]: https://github.com/iyasha/pysilpo/stargazers
[issues-shield]: https://img.shields.io/github/issues/iyasha/pysilpo.svg?style=for-the-badge
[issues-url]: https://github.com/iyasha/pysilpo/issues
[license-shield]: https://img.shields.io/github/license/iyasha/pysilpo.svg?style=for-the-badge
[license-url]: https://github.com/iyasha/pysilpo/blob/master/LICENSE