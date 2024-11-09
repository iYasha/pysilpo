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
    <a href="https://pysilpo.readthedocs.io">Documentation</a>
    .
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

### Get authorized user cheques

```python
from pysilpo import Silpo
from datetime import datetime

silpo = Silpo(phone_number="+380123456789")

cheques = silpo.cheque.all(
    date_from=datetime(2024, 7, 19), date_to=datetime(2024, 8, 19)
)

for cheque in cheques:
    print(cheque.sum_balance)
    print(cheque.detail.positions)
```

### Get Silpo products

```python
from pysilpo import Silpo

for product in Silpo.product.all():
    print(product.title)
```

## Change Log

### 2.0.0
- Added OpenID OTP authorization support with cached session and token refresh mechanism
- Cheque API now more clear and using RestFul API
- Debug mode now supported!

### 0.1.2
- Fix: `APIClient.get` might return None

### 0.1.1
- Silpo changed API domain to graphql.silpo.ua

### 0.1.0
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

## License
Distributed under the Apache2 License. See `LICENSE` for more information.

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
[license-url]: https://github.com/iyasha/pysilpo/blob/main/LICENSE
