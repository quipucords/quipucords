import React, { Component } from 'react';

class VerticalNavigation extends Component {
  render() {
    return (
      <div className="nav-pf-vertical nav-pf-vertical-with-sub-menus">
        <ul className="list-group">
          <li className="list-group-item">
            <a href="#0">
              <span className="pficon pficon-network" data-toggle="tooltip" title="Sources"></span>
              <span className="list-group-item-value">Sources</span>
            </a>
          </li>
          <li className="list-group-item">
            <a href="#0">
              <span className="fa fa-list-alt" data-toggle="tooltip" title="Scans"></span>
              <span className="list-group-item-value">Scans</span>
            </a>
          </li>
        </ul>
      </div>
    );
  }
  }

  export default VerticalNavigation;