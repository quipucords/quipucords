import React, { Component } from 'react';
import Masthead from './masthead/masthead'
import VerticalNavigation from './verticalNavigation/verticalNavigation'
import Content from './content/content';
import { getMenu } from '../routes'
import './app.css';

class App extends Component {
  constructor() {
    super();
    this.menu = getMenu();
  }

  render() {
    return (
      <div>
        <Masthead />
        <VerticalNavigation menuItems={this.menu}/>
        <Content/>
      </div>
    );
  }
}

export default App;
