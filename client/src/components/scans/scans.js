import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';

import {
  Alert,
  Grid,
  EmptyState,
  Row,
  ListView,
  Modal
} from 'patternfly-react';

import { bindMethods } from '../../common/helpers';
import Store from '../../redux/store';
import { toastNotificationTypes } from '../../redux/constants';
import { getScans } from '../../redux/actions/scansActions';

import ScansToolbar from './scansToolbar';
import SourcesEmptyState from '../sources/sourcesEmptyState';
import { ScanListItem } from './scanListItem';

class Scans extends React.Component {
  constructor() {
    super();

    bindMethods(this, [
      'runScans',
      'repeatScans',
      'downloadScans',
      'itemSelectChange',
      'addSource',
      'importSources',
      'refresh'
    ]);
    this.state = {
      filteredItems: [],
      selectedItems: []
    };
  }

  componentDidMount() {
    this.props.getScans();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.scans !== this.props.scans) {
      // Reset selection state though we may want to keep selections over refreshes...
      nextProps.scans.forEach(scan => {
        scan.selected = false;
      });

      let filteredItems = this.filterScans(
        nextProps.scans,
        nextProps.activeFilters
      );

      this.setState({ filteredItems: filteredItems, selectedItems: [] });
    } else if (nextProps.activeFilters !== this.props.activeFilters) {
      let filteredItems = this.filterScans(
        nextProps.scans,
        nextProps.activeFilters
      );
      this.setState({ filteredItems: filteredItems });
    }
  }

  matchesFilter(item, filter) {
    let re = new RegExp(filter.value, 'i');

    switch (filter.field.id) {
      case 'name':
        return (item.id + '').match(re) !== null; // Using ID for now until we get a name
      case 'status':
        return item.status === filter.value.id;
      case 'scanType':
        return item.scan_type === filter.value.id;
      default:
        return true;
    }
  }

  matchesFilters(item, filters) {
    let matches = true;

    filters.forEach(filter => {
      if (!this.matchesFilter(item, filter)) {
        matches = false;
        return false;
      }
    });
    return matches;
  }

  filterScans(scans, filters) {
    return scans.filter(item => {
      return this.matchesFilters(item, filters);
    });
  }

  sortScans(items) {
    const { sortType, sortAscending } = this.props;

    let sortId = sortType ? sortType.id : 'name';

    items.sort((item1, item2) => {
      let compValue;
      switch (sortId) {
        case 'name':
          compValue = item1.id - item2.id; // Using ID for now until we get a name
          break;
        case 'status':
          compValue = item1.status.localeCompare(item2.status);
          if (compValue === 0) {
            compValue = item1.scan_type.localeCompare(item2.scan_type);
          }
          break;
        case 'scanType':
          compValue = item1.scan_type.localeCompare(item2.scan_type);
          if (compValue === 0) {
            compValue = item1.status.localeCompare(item2.status);
          }
          break;
        case 'sourceCount':
          compValue = item1.sources.length - item2.sources.length;
          if (compValue === 0) {
            compValue = item1.status.localeCompare(item2.status);
            if (compValue === 0) {
              compValue = item1.scan_type.localeCompare(item2.scan_type);
            }
          }
          break;
        default:
          compValue = 0;
      }

      if (!sortAscending) {
        compValue = compValue * -1;
      }

      return compValue;
    });
  }

  runScans() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Running scans is not yet implemented'
    });
  }

  repeatScans() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Repeating scans is not yet implemented'
    });
  }

  downloadScans() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Downloading scans is not yet implemented'
    });
  }

  itemSelectChange(item) {
    const { filteredItems } = this.state;

    item.selected = !item.selected;
    let selectedItems = filteredItems.filter(item => {
      return item.selected === true;
    });

    this.setState({ selectedItems: selectedItems });
  }

  addSource() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Adding sources is not yet implemented'
    });
  }

  importSources() {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: 'NYI',
      message: 'Importing sources is not yet implemented'
    });
  }

  refresh() {
    this.props.getScans();
  }

  renderList(items) {
    return (
      <Row>
        <ListView className="quipicords-list-view">
          {items.map((item, index) => (
            <ScanListItem
              item={item}
              key={index}
              onItemSelectChange={this.itemSelectChange}
            />
          ))}
        </ListView>
      </Row>
    );
  }

  render() {
    const { loading, loadError, errorMessage, scans } = this.props;
    const { filteredItems, selectedItems } = this.state;

    if (loading) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading scans...</div>
          </Modal.Body>
        </Modal>
      );
    }
    if (loadError) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving scans: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }
    if (scans && scans.length) {
      this.sortScans(filteredItems);

      return [
        <ScansToolbar
          totalCount={scans.length}
          filteredCount={filteredItems.length}
          key={1}
          runScansAvailable={selectedItems && selectedItems.length > 0}
          onRunScans={this.runScans}
          repeatScansAvailable={selectedItems && selectedItems.length > 0}
          onRepeatScans={this.repeatScans}
          downloadScansAvailable={selectedItems && selectedItems.length > 0}
          onDownloadScans={this.downloadScans}
          onRefresh={this.refresh}
        />,
        <Grid fluid key={2}>
          {this.renderList(filteredItems)}
        </Grid>
      ];
    }
    return (
      <SourcesEmptyState
        onAddSource={this.addSource}
        onImportSources={this.importSources}
      />
    );
  }
}

Scans.propTypes = {
  getScans: PropTypes.func,
  loadError: PropTypes.bool,
  errorMessage: PropTypes.string,
  loading: PropTypes.bool,
  scans: PropTypes.array,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

Scans.defaultProps = {
  loading: true
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getScans: () => dispatch(getScans())
});

function mapStateToProps(state) {
  return {
    loading: state.scans.loading,
    scans: state.scans.data,
    loadError: state.scans.error,
    errorMessage: state.scans.errorMessage,
    activeFilters: state.scansToolbar.activeFilters,
    sortType: state.scansToolbar.sortType,
    sortAscending: state.scansToolbar.sortAscending
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Scans);
