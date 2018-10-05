import { factsTypes } from '../constants';
import factsService from '../../services/factsService';

const addFacts = data => dispatch =>
  dispatch({
    type: factsTypes.ADD_FACTS,
    payload: factsService.addFacts(data)
  });

export { addFacts as default, addFacts };
