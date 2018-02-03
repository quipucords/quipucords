import PropTypes from 'prop-types';
import React from 'react';
import { connect } from 'react-redux';
import Store from '../../redux/store';

import {
  Alert,
  EmptyState,
  Grid,
  ListView,
  Modal,
  Row
} from 'patternfly-react';

import { getSources } from '../../redux/actions/sourcesActions';
import {
  toastNotificationTypes,
  confirmationModalTypes
} from '../../redux/constants';
import { bindMethods } from '../../common/helpers';

import SourcesToolbar from './sourcesToolbar';
import SourcesEmptyState from './sourcesEmptyState';
import { SourceListItem } from './sourceListItem';
import { CreateScanDialog } from './createScanDialog';
import { AddSourceWizard } from './addSourceWizard';

class Sources extends React.Component {
  constructor() {
    super();

    bindMethods(this, [
      'importSources',
      'scanSource',
      'scanSources',
      'itemSelectChange',
      'editSource',
      'deleteSource',
      'hideScanDialog',
      'createScan',
      'refresh',
      'showAddSourceWizard',
      'quitAddSourceWizard'
    ]);

    this.state = {
      filteredItems: [],
      selectedItems: [],
      scanDialogShown: false,
      multiSourceScan: false,
      currentScanSource: null,
      addSourceWizardShown: false
    };
  }

  componentDidMount() {
    this.props.getSources();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.sources !== this.props.sources) {
      // Reset selection state though we may want to keep selections over refreshes...
      nextProps.sources.forEach(source => {
        source.selected = false;
      });

      // TODO: Remove once we get real failed host data
      nextProps.sources.forEach(source => {
        let failedCount = Math.floor(Math.random() * 10);
        source.failed_hosts = [];
        for (let i = 0; i < failedCount; i++) {
          source.failed_hosts.push('failedHost' + (i + 1));
        }
      });

      let filteredItems = this.filterSources(
        nextProps.sources,
        nextProps.activeFilters
      );

      this.setState({ filteredItems: filteredItems, selectedItems: [] });
    } else if (nextProps.activeFilters !== this.props.activeFilters) {
      let filteredItems = this.filterSources(
        nextProps.sources,
        nextProps.activeFilters
      );
      this.setState({ filteredItems: filteredItems });
    }
  }

  matchesFilter(item, filter) {
    let re = new RegExp(filter.value, 'i');

    switch (filter.field.id) {
      case 'name':
        return item.name.match(re) !== null;
      case 'sourceType':
        return item.source_type === filter.value.id;
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

  filterSources(sources, filters) {
    if (!filters || filters.length === 0) {
      return sources;
    }

    return sources.filter(item => {
      return this.matchesFilters(item, filters);
    });
  }

  sortSources(items) {
    const { sortType, sortAscending } = this.props;

    let sortId = sortType ? sortType.id : 'name';

    items.sort((item1, item2) => {
      let compValue;
      switch (sortId) {
        case 'name':
          compValue = item1.name.localeCompare(item2.name);
          break;
        case 'sourceType':
          compValue = item1.source_type.localeCompare(item2.source_type);
          break;
        case 'hostCount':
          compValue = item1.hosts.length - item2.hosts.length;
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

  showAddSourceWizard() {
    this.setState({ addSourceWizardShown: true });
  }

  quitAddSourceWizard() {
    let onConfirm = () => {
      Store.dispatch({
        type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
      });

      this.setState({ addSourceWizardShown: false });
    };

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Cancel Add Source',
      heading: 'Are you sure you want to exit this wizard?',
      body: 'Exiting this wizard will cancel adding the source.',
      cancelButtonText: 'No',
      confirmButtonText: 'Yes',
      onConfirm: onConfirm
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

  scanSource(source) {
    this.setState({
      scanDialogShown: true,
      multiSourceScan: false,
      currentScanSource: source
    });
  }

  scanSources() {
    this.setState({ scanDialogShown: true, multiSourceScan: true });
  }

  hideScanDialog() {
    this.setState({ scanDialogShown: false });
  }

  itemSelectChange(item) {
    const { filteredItems } = this.state;

    item.selected = !item.selected;
    let selectedItems = filteredItems.filter(item => {
      return item.selected === true;
    });

    this.setState({ selectedItems: selectedItems });
  }

  editSource(item) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.name,
      message: 'Editing sources is not yet implemented'
    });
  }

  doDeleteSource(item) {
    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_HIDE
    });

    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: item.name,
      message: 'Deleting sources is not yet implemented'
    });
  }

  deleteSource(item) {
    let heading = (
      <span>
        Are you sure you want to delete the source <strong>{item.name}</strong>?
      </span>
    );

    let onConfirm = () => this.doDeleteSource(item);

    Store.dispatch({
      type: confirmationModalTypes.CONFIRMATION_MODAL_SHOW,
      title: 'Delete Source',
      heading: heading,
      confirmButtonText: 'Delete',
      onConfirm: onConfirm
    });
  }

  createScan(scanName, sources) {
    Store.dispatch({
      type: toastNotificationTypes.TOAST_ADD,
      alertType: 'error',
      header: scanName,
      message: 'Scanning sources is not yet implemented'
    });
    this.hideScanDialog();
  }

  refresh() {
    this.props.getSources();
  }

  renderList(items) {
    return (
      <Row>
        <ListView className="quipicords-list-view">
          {items.map((item, index) => (
            <SourceListItem
              item={item}
              key={index}
              onItemSelectChange={this.itemSelectChange}
              onEdit={this.editSource}
              onDelete={this.deleteSource}
              onScan={this.scanSource}
            />
          ))}
        </ListView>
      </Row>
    );
  }

  render() {
    const { loading, loadError, errorMessage, sources } = this.props;
    const {
      filteredItems,
      selectedItems,
      scanDialogShown,
      multiSourceScan,
      currentScanSource,
      addSourceWizardShown
    } = this.state;

    if (loading) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading sources...</div>
          </Modal.Body>
        </Modal>
      );
    }

    if (loadError) {
      return (
        <EmptyState>
          <Alert type="error">
            <span>Error retrieving sources: {errorMessage}</span>
          </Alert>
        </EmptyState>
      );
    }

    if (sources && sources.length) {
      this.sortSources(filteredItems);

      return (
        <React.Fragment>
          <SourcesToolbar
            totalCount={sources.length}
            filteredCount={filteredItems.length}
            key={1}
            onAddSource={this.showAddSourceWizard}
            scanAvailable={selectedItems && selectedItems.length > 0}
            onScan={this.scanSources}
            onRefresh={this.refresh}
          />
          <Grid fluid key={2}>
            {this.renderList(filteredItems)}
          </Grid>
          <AddSourceWizard
            show={addSourceWizardShown}
            onCancel={this.quitAddSourceWizard}
          />
          <CreateScanDialog
            key="createScanDialog"
            show={scanDialogShown}
            sources={multiSourceScan ? selectedItems : [currentScanSource]}
            onCancel={this.hideScanDialog}
            onScan={this.createScan}
          />
        </React.Fragment>
      );
    }

    return (
      <React.Fragment>
        <SourcesEmptyState
          onAddSource={this.showAddSourceWizard}
          onImportSources={this.importSources}
        />
        <AddSourceWizard
          show={addSourceWizardShown}
          onCancel={this.quitAddSourceWizard}
        />
      </React.Fragment>
    );
  }
}

Sources.propTypes = {
  getSources: PropTypes.func,
  loadError: PropTypes.bool,
  errorMessage: PropTypes.string,
  loading: PropTypes.bool,
  sources: PropTypes.array,
  activeFilters: PropTypes.array,
  sortType: PropTypes.object,
  sortAscending: PropTypes.bool
};

Sources.defaultProps = {
  loading: true
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getSources: () => dispatch(getSources())
});

function mapStateToProps(state) {
  return {
    loading: state.sources.loading,
    sources: state.sources.data,
    loadError: state.sources.error,
    errorMessage: state.sources.errorMessage,
    activeFilters: state.sourcesToolbar.activeFilters,
    sortType: state.sourcesToolbar.sortType,
    sortAscending: state.sourcesToolbar.sortAscending
  };
}

export default connect(mapStateToProps, mapDispatchToProps)(Sources);
