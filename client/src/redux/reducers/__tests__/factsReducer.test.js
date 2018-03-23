import helpers from '../../../common/helpers';
import { factsTypes } from '../../constants/index';
import factsReducer from '../factsReducer';

const initialState = {
  persist: {},

  update: {
    error: false,
    errorMessage: '',
    pending: false,
    fulfilled: false,
    facts: {}
  }
};

describe('factsReducer', function() {
  it('should return the initial state', () => {
    expect(factsReducer(undefined, {})).toEqual(initialState);
  });

  it('should handle ADD_FACTS_REJECTED', () => {
    let dispatched = {
      type: helpers.REJECTED_ACTION(factsTypes.ADD_FACTS),
      error: true,
      payload: {
        message: 'BACKUP MESSAGE',
        response: {
          data: {
            detail: 'GET ERROR'
          }
        }
      }
    };

    let resultState = factsReducer(undefined, dispatched);
    expect(resultState.update.error).toBeTruthy();
    expect(resultState.update.errorMessage).toEqual('GET ERROR');

    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle ADD_FACTS_PENDING', () => {
    let dispatched = {
      type: helpers.PENDING_ACTION(factsTypes.ADD_FACTS)
    };

    let resultState = factsReducer(undefined, dispatched);

    expect(resultState.update.pending).toBeTruthy();
    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle ADD_FACTS_FULFILLED', () => {
    let dispatched = {
      type: helpers.FULFILLED_ACTION(factsTypes.ADD_FACTS),
      payload: {
        data: [
          {
            name: '1',
            id: 1
          },
          {
            name: '2',
            id: 2
          },
          {
            name: '3',
            id: 3
          },
          {
            name: '4',
            id: 4
          }
        ]
      }
    };

    let resultState = factsReducer(undefined, dispatched);

    expect(resultState.update.fulfilled).toBeTruthy();
    expect(resultState.update.facts).toHaveLength(4);

    expect(resultState.persist).toEqual(initialState.persist);
  });
});
