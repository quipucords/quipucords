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
      type: factsTypes.ADD_FACTS_REJECTED,
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
      type: factsTypes.ADD_FACTS_PENDING
    };

    let resultState = factsReducer(undefined, dispatched);

    expect(resultState.update.pending).toBeTruthy();
    expect(resultState.persist).toEqual(initialState.persist);
  });

  it('should handle ADD_FACTS_FULFILLED', () => {
    let dispatched = {
      type: factsTypes.ADD_FACTS_FULFILLED,
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
