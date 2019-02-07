import promiseMiddleware from 'redux-promise-middleware';
import { applyMiddleware, combineReducers, createStore } from 'redux';
import moxios from 'moxios';
import { factsReducer } from '../../reducers';
import { factsActions } from '..';

describe('FactsActions', () => {
  const middleware = [promiseMiddleware()];
  const generateStore = () =>
    createStore(
      combineReducers({
        facts: factsReducer
      }),
      applyMiddleware(...middleware)
    );

  beforeEach(() => {
    moxios.install();

    moxios.wait(() => {
      const request = moxios.requests.mostRecent();
      request.respondWith({
        status: 200,
        response: {
          test: 'success'
        }
      });
    });
  });

  afterEach(() => {
    moxios.uninstall();
  });

  it('Should return response content for addFacts method', done => {
    const store = generateStore();
    const dispatcher = factsActions.addFacts();

    dispatcher(store.dispatch).then(() => {
      const response = store.getState().facts;

      expect(response.update.facts.test).toEqual('success');
      done();
    });
  });
});
