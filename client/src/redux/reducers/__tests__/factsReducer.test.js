import factsReducer from '../factsReducer';
import { factsTypes as types } from '../../constants';
import helpers from '../../../common/helpers';

describe('factsReducer', () => {
  it('should return the initial state', () => {
    expect(factsReducer.initialState).toBeDefined();
  });

  it('should handle all defined error types', () => {
    const specificTypes = [types.ADD_FACTS];

    specificTypes.forEach(value => {
      const dispatched = {
        type: helpers.REJECTED_ACTION(value),
        error: true,
        payload: {
          message: 'MESSAGE',
          response: {
            status: 0,
            statusText: 'ERROR TEST',
            data: {
              detail: 'ERROR'
            }
          }
        }
      };

      const resultState = factsReducer(undefined, dispatched);

      expect({ type: helpers.REJECTED_ACTION(value), result: resultState }).toMatchSnapshot(`rejected types ${value}`);
    });
  });

  it('should handle all defined pending types', () => {
    const specificTypes = [types.ADD_FACTS];

    specificTypes.forEach(value => {
      const dispatched = {
        type: helpers.PENDING_ACTION(value)
      };

      const resultState = factsReducer(undefined, dispatched);

      expect({ type: helpers.PENDING_ACTION(value), result: resultState }).toMatchSnapshot(`pending types ${value}`);
    });
  });

  it('should handle all defined fulfilled types', () => {
    const specificTypes = [types.ADD_FACTS];

    specificTypes.forEach(value => {
      const dispatched = {
        type: helpers.FULFILLED_ACTION(value),
        payload: {
          data: {
            test: 'success'
          }
        }
      };

      const resultState = factsReducer(undefined, dispatched);

      expect({ type: helpers.FULFILLED_ACTION(value), result: resultState }).toMatchSnapshot(
        `fulfilled types ${value}`
      );
    });
  });
});
