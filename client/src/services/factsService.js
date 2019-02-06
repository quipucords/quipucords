import axios from 'axios';
import serviceConfig from './config';

const addFacts = (data = {}) =>
  axios(
    serviceConfig({
      method: 'post',
      url: `${process.env.REACT_APP_FACTS_SERVICE}`,
      data
    })
  );

const factsService = {
  addFacts
};

export { factsService as default, factsService, addFacts };
