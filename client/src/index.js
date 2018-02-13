import React from 'react';
import ReactDOM from 'react-dom';
import { Provider } from 'react-redux';
import { BrowserRouter as Router } from 'react-router-dom';

import 'rcue/dist/css/rcue.css';
import 'rcue/dist/css/rcue-additions.css';
import './styles/css/entitlements.css';

import App from './components/app';
import { baseName } from './routes';
import store from './redux/store';

// ToDo: Evaluate the need for being offline, causes authentication errors

ReactDOM.render(
  <Provider store={store}>
    <Router basename={baseName}>
      <App />
    </Router>
  </Provider>,
  document.getElementById('root')
);
