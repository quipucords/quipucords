import axios from 'axios';

class FactsService {
  static addFacts(data = {}) {
    return axios({
      method: 'post',
      url: `${process.env.REACT_APP_FACTS_SERVICE}`,
      xsrfCookieName: process.env.REACT_APP_AUTH_TOKEN,
      xsrfHeaderName: process.env.REACT_APP_AUTH_HEADER,
      data: data
    });
  }
}

export default FactsService;
