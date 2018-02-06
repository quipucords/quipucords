import { createStore, applyMiddleware } from 'redux';
import thunkMiddleware from 'redux-thunk';
import reduxReducers from './reducers';
import promiseMiddleware from 'redux-promise-middleware';

const hydrateStore = () => {
  // Create any initial state items based on stored data (cookies etc.)
  return {};
};

const store = createStore(
  reduxReducers,
  hydrateStore(),
  applyMiddleware(thunkMiddleware, promiseMiddleware())
);

export default store;
